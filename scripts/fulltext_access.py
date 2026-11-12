#!/usr/bin/env python3
"""
Legal full-text access ladder for literature-backed curation.

All requests use anonymous User-Agent strings (no email address disclosure,
no mailto query parameters) in compliance with standing privacy agreements.

Ladder of legal rungs (checked in order):
  1. Zotero local storage  — check ~/Zotero/storage/*/ for already-saved PDFs
                             via ~/Zotero/zotero.sqlite (read-only immutable URI).
  2. Europe PMC            — fullTextXML / open-access PDF via PMCID.
  3. Unpaywall (anonymous) — legal OA location (repository or publisher bronze/gold/hybrid)
                             via CrossRef / OpenAlex / Europe PMC OA flags (no email needed).
  4. OpenAlex Works API    — anonymous `best_oa_location` / `locations` PDF URLs.
  5. OSTI.gov API v1       — DOE Office of Scientific and Technical Information
                             accepted manuscripts / technical reports by DOI or title.
  6. CrossRef TDM links    — publisher text-and-data-mining full-text links;
                             supports Elsevier `X-ELS-APIKey` and Wiley
                             `Wiley-TDM-Client-Token` when configured in env.
  7. LBNL / UC library     — UC eLinks / LibKey / institutional proxy / EZProxy URLs
                             when `LBNL_LIBKEY_ID` + `LBNL_LIBKEY_TOKEN` or
                             `LBNL_PROXY_PREFIX` are configured, plus publisher
                             campus-IP direct PDF endpoints when on LBNL network.
  8. CORE API v3           — aggregated repository full text when `CORE_API_KEY` is set.
  9. Semantic Scholar      — `openAccessPdf` via anonymous Graph API v1.
 10. Author / lab / preprint search — Europe PMC preprint servers (bioRxiv / medRxiv /
                             Research Square / ChemRxiv) and CrossRef relation links.

Staging rule:
  Downloaded full text MUST be staged under gitignored `.temp/fulltext/`
  (never committed, never placed under `references_cache/`).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

USER_AGENT = "LiteratureCurationBot/1.0 (https://github.com/CultureBotAI)"
DOI_RESOLVER_RE = re.compile(r"https?://(dx\.)?doi\.org/", re.IGNORECASE)
DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGING_ROOT = REPO_ROOT / ".temp" / "fulltext"
FORBIDDEN_REPO_DIRS = frozenset(
    {
        "references_cache",
        "src",
        "tests",
        "docs",
        "conf",
        "scripts",
        "schema",
        "prompts",
        ".git",
        ".github",
    }
)


@dataclass
class AccessAttempt:
    rung: str
    status: str  # "found" | "not_found" | "skipped" | "error"
    url: Optional[str] = None
    content_type: Optional[str] = None
    note: Optional[str] = None


@dataclass
class AccessReport:
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    title: Optional[str] = None
    fulltext_available: bool = False
    best_rung: Optional[str] = None
    best_url: Optional[str] = None
    local_staged_path: Optional[str] = None
    attempts: list[AccessAttempt] = field(default_factory=list)
    manual_fallback_instructions: list[str] = field(default_factory=list)


def _http_get_json(
    url: str,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 15,
) -> Optional[dict | list]:
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _clean_doi(doi: str) -> str:
    d = (doi or "").strip()
    while True:
        updated = DOI_PREFIX_RE.sub("", d).strip()
        if updated == d:
            break
        d = updated
    return d


def _escape_core_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def epmc_core(
    pmid: Optional[str] = None,
    pmcid: Optional[str] = None,
    doi: Optional[str] = None,
) -> Optional[dict]:
    if pmid:
        query = f"EXT_ID:{pmid} AND SRC:MED"
    elif pmcid:
        query = f"PMCID:{pmcid}"
    elif doi:
        cleaned = _clean_doi(doi)
        if not cleaned:
            return None
        query = f'DOI:"{cleaned}"'
    else:
        return None
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={urllib.parse.quote(query)}&resultType=core&format=json&pageSize=1"
    )
    data = _http_get_json(url)
    if not isinstance(data, dict):
        return None
    results = data.get("resultList", {}).get("result", [])
    return results[0] if results else None


def crossref_meta(doi: str) -> Optional[dict]:
    cleaned = _clean_doi(doi)
    if not cleaned:
        return None
    url = f"https://api.crossref.org/works/{urllib.parse.quote(cleaned, safe='')}"
    try:
        data = _http_get_json(url)
    except Exception:
        return None
    if isinstance(data, dict):
        return data.get("message")
    return None


def _zotero_data_dir() -> Path:
    return Path(os.environ.get("ZOTERO_DATA_DIR", str(Path.home() / "Zotero")))


def _resolve_zotero_storage_pdf(storage_dir: Path, candidate: Path) -> Optional[Path]:
    """Verify candidate is a regular, non-symlink PDF strictly inside storage_dir."""
    try:
        if storage_dir.is_symlink() or not storage_dir.is_dir():
            return None
        storage_root = storage_dir.resolve(strict=True)
        if candidate.is_symlink():
            return None
        for parent in candidate.parents:
            if parent == storage_dir or parent == storage_root:
                break
            if parent.is_symlink():
                return None
        resolved_pdf = candidate.resolve(strict=True)
        if not resolved_pdf.is_relative_to(storage_root) or resolved_pdf == storage_root:
            return None
        meta = resolved_pdf.lstat()
        if stat.S_ISLNK(meta.st_mode) or not stat.S_ISREG(meta.st_mode):
            return None
        if resolved_pdf.suffix.lower() != ".pdf":
            return None
        return resolved_pdf
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Rung 1: Local Zotero storage
# ---------------------------------------------------------------------------
def try_zotero_local(
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    title: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    """
    Search local Zotero SQLite database (read-only immutable mode) for a matching
    item with a local PDF attachment in ~/Zotero/storage/<KEY>/*.pdf.
    Returns (file_uri, note) if found.
    """
    zotero_dir = _zotero_data_dir()
    if zotero_dir.is_symlink():
        return None
    db_path = zotero_dir / "zotero.sqlite"
    storage_dir = zotero_dir / "storage"
    if (
        not db_path.exists()
        or db_path.is_symlink()
        or not storage_dir.exists()
        or storage_dir.is_symlink()
    ):
        return None

    uri = f"file:{urllib.parse.quote(str(db_path))}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=5)
    except Exception:
        return None

    try:
        cur = conn.cursor()
        candidate_item_ids: set[int] = set()

        if doi:
            clean = _clean_doi(doi).lower()
            cur.execute(
                """
                SELECT iv.itemID
                FROM itemData iv
                JOIN itemDataValues idv ON iv.valueID = idv.valueID
                JOIN fields f ON iv.fieldID = f.fieldID
                WHERE f.fieldName = 'DOI' AND lower(idv.value) LIKE ?
                """,
                (f"%{clean}%",),
            )
            candidate_item_ids.update(r[0] for r in cur.fetchall())

        if pmid and not candidate_item_ids:
            cur.execute(
                """
                SELECT iv.itemID
                FROM itemData iv
                JOIN itemDataValues idv ON iv.valueID = idv.valueID
                WHERE idv.value LIKE ?
                """,
                (f"%PMID: {pmid}%",),
            )
            candidate_item_ids.update(r[0] for r in cur.fetchall())

        if title and not candidate_item_ids and len(title) >= 12:
            cur.execute(
                """
                SELECT iv.itemID
                FROM itemData iv
                JOIN itemDataValues idv ON iv.valueID = idv.valueID
                JOIN fields f ON iv.fieldID = f.fieldID
                WHERE f.fieldName = 'title' AND lower(idv.value) = ?
                """,
                (title.strip().lower(),),
            )
            candidate_item_ids.update(r[0] for r in cur.fetchall())

        for parent_id in candidate_item_ids:
            cur.execute(
                """
                SELECT i.key, ia.path, ia.contentType
                FROM itemAttachments ia
                JOIN items i ON ia.itemID = i.itemID
                WHERE ia.parentItemID = ?
                """,
                (parent_id,),
            )
            for att_key, att_path, content_type in cur.fetchall():
                if not isinstance(att_key, str) or not att_key or "/" in att_key or "\\" in att_key:
                    continue
                if att_path:
                    if not isinstance(att_path, str) or not att_path.startswith("storage:"):
                        continue
                    rel_name = att_path[len("storage:") :]
                    if not rel_name:
                        continue
                    candidate = storage_dir / att_key / rel_name
                    safe_pdf = _resolve_zotero_storage_pdf(storage_dir, candidate)
                    if safe_pdf is not None:
                        return f"file://{safe_pdf}", f"Zotero local storage ({att_key})"
                key_dir = storage_dir / att_key
                if key_dir.is_dir() and not key_dir.is_symlink():
                    for p in sorted(key_dir.glob("*.pdf")):
                        safe_pdf = _resolve_zotero_storage_pdf(storage_dir, p)
                        if safe_pdf is not None:
                            return f"file://{safe_pdf}", f"Zotero local storage ({att_key})"
    except Exception:
        return None
    finally:
        conn.close()
    return None


# ---------------------------------------------------------------------------
# Rung 2: Europe PMC XML / OA PDF
# ---------------------------------------------------------------------------
def try_epmc_fulltext(rec: Optional[dict]) -> Optional[tuple[str, str, str]]:
    """Returns (url, content_type, note) if Europe PMC has full text XML or OA PDF."""
    if not rec:
        return None
    pmcid = rec.get("pmcid")
    is_oa = rec.get("isOpenAccess") == "Y"
    in_epmc = rec.get("inEPMC") == "Y"
    if pmcid and (is_oa or in_epmc):
        xml_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        return xml_url, "application/xml", f"Europe PMC fullTextXML ({pmcid})"
    ft_urls = rec.get("fullTextUrlList", {}).get("fullTextUrl", [])
    for entry in ft_urls:
        avail = (entry.get("availabilityCode") or "").upper()
        style = (entry.get("documentStyle") or "").lower()
        url = entry.get("url")
        if url and avail in {"OA", "F"} and style in {"pdf", "html", "doi"}:
            return url, style, f"Europe PMC free fullTextUrl ({avail}/{style})"
    return None


# ---------------------------------------------------------------------------
# Rung 3: OpenAlex Works API (anonymous OA locations)
# ---------------------------------------------------------------------------
def try_openalex_oa(doi: str) -> Optional[tuple[str, str]]:
    """Query OpenAlex Works API anonymously for open-access PDF or landing URL."""
    clean = _clean_doi(doi)
    if not clean:
        return None
    url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(clean, safe='/')}"
    try:
        data = _http_get_json(url)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    best = data.get("best_oa_location") or {}
    pdf_url = best.get("pdf_url")
    if pdf_url:
        host = best.get("host_type") or "oa"
        return pdf_url, f"OpenAlex best_oa_location PDF ({host})"

    for loc in data.get("locations") or []:
        if loc.get("is_oa") and loc.get("pdf_url"):
            return loc["pdf_url"], "OpenAlex OA location PDF"

    oa_url = (data.get("open_access") or {}).get("oa_url")
    if oa_url and not DOI_RESOLVER_RE.match(oa_url):
        return oa_url, "OpenAlex open_access.oa_url"
    return None


# ---------------------------------------------------------------------------
# Rung 4: DOE OSTI.gov API v1 (accepted manuscripts & DOE reports)
# ---------------------------------------------------------------------------
def try_osti(
    doi: Optional[str] = None,
    title: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    """Query OSTI.gov API v1 for free DOE-funded full text."""
    params: dict[str, str] = {}
    if doi:
        params["doi"] = _clean_doi(doi)
    elif title:
        params["q"] = title
    else:
        return None
    url = f"https://www.osti.gov/api/v1/records?{urllib.parse.urlencode(params)}"
    try:
        records = _http_get_json(url)
    except Exception:
        return None
    if not isinstance(records, list):
        return None
    for rec in records:
        if not isinstance(rec, dict):
            continue
        osti_id = rec.get("osti_id")
        links = rec.get("links") or []
        for link in links:
            if isinstance(link, dict) and link.get("rel") in {"fulltext", "citation"}:
                href = link.get("href")
                if href and "doi.org/" not in href:
                    return href, f"OSTI.gov ({osti_id}, rel={link.get('rel')})"
        if osti_id:
            return f"https://www.osti.gov/servlets/purl/{osti_id}", f"OSTI.gov purl ({osti_id})"
    return None


# ---------------------------------------------------------------------------
# Rung 5: CrossRef TDM & Publisher APIs (Elsevier / Wiley / Springer / Vor)
# ---------------------------------------------------------------------------
def try_crossref_tdm(doi: str, cr_msg: Optional[dict] = None) -> Optional[tuple[str, str]]:
    """
    Check CrossRef `link` array and publisher TDM APIs.
    Uses `ELSEVIER_API_KEY` (`X-ELS-APIKey`) or `WILEY_TDM_TOKEN` when present
    in environment, or open Vor/TDM links when unauthenticated.
    """
    clean = _clean_doi(doi)
    if not clean:
        return None
    els_key = os.environ.get("ELSEVIER_API_KEY") or os.environ.get("ELS_API_KEY")
    wiley_token = os.environ.get("WILEY_TDM_TOKEN") or os.environ.get("WILEY_TDM_CLIENT_TOKEN")

    if clean.startswith("10.1016/") and els_key:
        els_url = (
            f"https://api.elsevier.com/content/article/doi/{urllib.parse.quote(clean)}"
            "?httpAccept=text/xml"
        )
        return els_url, "Elsevier Article Retrieval API (ELSEVIER_API_KEY configured)"

    if clean.startswith(("10.1002/", "10.1111/")) and wiley_token:
        wiley_url = f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{urllib.parse.quote(clean, safe='')}"
        return wiley_url, "Wiley TDM API (WILEY_TDM_TOKEN configured)"

    msg = cr_msg if cr_msg is not None else crossref_meta(clean)
    if not isinstance(msg, dict):
        return None

    for link in msg.get("link") or []:
        if not isinstance(link, dict):
            continue
        url = link.get("URL")
        ctype = (link.get("content-type") or "").lower()
        app = (link.get("intended-application") or "").lower()
        if not url:
            continue
        if "api.elsevier.com" in url and not els_key:
            continue
        if "api.wiley.com" in url and not wiley_token:
            continue
        if app in {"similarity-checking", "text-mining"} or "pdf" in ctype or "xml" in ctype:
            return url, f"CrossRef link ({app or 'direct'}, {ctype or 'unknown'})"
    return None


# ---------------------------------------------------------------------------
# Rung 6: LBNL / UC Library (LibKey Nomad API or Institutional Proxy)
# ---------------------------------------------------------------------------
def try_lbnl_library(doi: str) -> Optional[tuple[str, str]]:
    """
    Check Third Iron LibKey API if `LBNL_LIBKEY_ID` and `LBNL_LIBKEY_TOKEN`
    are set in the environment, or construct an institutional proxy URL if
    `LBNL_PROXY_PREFIX` is set.
    """
    clean = _clean_doi(doi)
    if not clean:
        return None
    libkey_id = os.environ.get("LBNL_LIBKEY_ID")
    libkey_token = os.environ.get("LBNL_LIBKEY_TOKEN")
    if libkey_id and libkey_token:
        url = (
            f"https://public-api.thirdiron.com/public/v1/libraries/{libkey_id}"
            f"/articles/doi/{urllib.parse.quote(clean, safe='/')}"
            f"?access_token={urllib.parse.quote(libkey_token)}"
        )
        try:
            data = _http_get_json(url)
            if isinstance(data, dict):
                inner = data.get("data") or {}
                ft_file = inner.get("fullTextFile")
                content_loc = inner.get("contentLocation")
                if ft_file:
                    return ft_file, "LBNL LibKey fullTextFile PDF"
                if content_loc:
                    return content_loc, "LBNL LibKey contentLocation"
        except Exception:
            pass

    proxy_prefix = os.environ.get("LBNL_PROXY_PREFIX")
    if proxy_prefix:
        target = f"https://doi.org/{clean}"
        return f"{proxy_prefix.rstrip('/')}/{target}", "LBNL institutional proxy (LBNL_PROXY_PREFIX)"
    return None


# ---------------------------------------------------------------------------
# Rung 7: CORE API v3 (aggregated repository full text)
# ---------------------------------------------------------------------------
def try_core(doi: Optional[str] = None, title: Optional[str] = None) -> Optional[tuple[str, str]]:
    api_key = (os.environ.get("CORE_API_KEY") or "").strip()
    if not api_key:
        return None
    if doi:
        cleaned = _clean_doi(doi)
        if not cleaned:
            return None
        q = f'doi:"{_escape_core_literal(cleaned)}"'
    elif title:
        cleaned_title = title.strip()
        if not cleaned_title:
            return None
        q = f'title:"{_escape_core_literal(cleaned_title)}"'
    else:
        return None
    url = f"https://api.core.ac.uk/v3/search/works?q={urllib.parse.quote(q)}&limit=1"
    try:
        data = _http_get_json(url, headers={"Authorization": f"Bearer {api_key}"})
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    for item in data.get("results") or []:
        dl = item.get("downloadUrl")
        if dl:
            return dl, "CORE v3 repository downloadUrl"
    return None


# ---------------------------------------------------------------------------
# Rung 8: Semantic Scholar Graph API v1 (anonymous openAccessPdf)
# ---------------------------------------------------------------------------
def try_semantic_scholar(
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    if doi:
        cleaned = _clean_doi(doi)
        if not cleaned:
            return None
        paper_id = f"DOI:{cleaned}"
    elif pmid:
        paper_id = f"PMID:{pmid}"
    else:
        return None
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/{urllib.parse.quote(paper_id, safe=':/')}"
        "?fields=openAccessPdf,isOpenAccess"
    )
    try:
        data = _http_get_json(url)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    oa_pdf = (data.get("openAccessPdf") or {}).get("url")
    if oa_pdf:
        return oa_pdf, "Semantic Scholar openAccessPdf"
    return None


# ---------------------------------------------------------------------------
# Rung 9: ACS Figshare Supporting Information (10.1021/<suffix>.s001)
# ---------------------------------------------------------------------------
def try_acs_figshare_si(doi: Optional[str] = None) -> Optional[tuple[str, str]]:
    if not doi:
        return None
    clean_doi = _clean_doi(doi)
    if not clean_doi or not clean_doi.startswith("10.1021/"):
        return None
    base_doi = re.sub(r"\.s\d{3}$", "", clean_doi, flags=re.IGNORECASE)
    for suffix in (".s001", ".s002"):
        si_doi = f"{base_doi}{suffix}"
        handle_url = "https://doi.org/api/handles/" + urllib.parse.quote(si_doi, safe="/")
        try:
            handle_data = _http_get_json(handle_url)
        except Exception:
            continue
        if not isinstance(handle_data, dict) or handle_data.get("responseCode") != 1:
            continue
        target_url = None
        for val in handle_data.get("values") or []:
            if isinstance(val, dict) and val.get("type") == "URL":
                data_val = (val.get("data") or {}).get("value")
                if isinstance(data_val, str) and data_val.startswith("https://"):
                    target_url = data_val
                    break
        if not target_url:
            continue
        m = re.search(r"figshare\.com/articles/[^/]+/[^/]+/(\d+)", target_url)
        if m:
            article_id = m.group(1)
            try:
                meta = _http_get_json(f"https://api.figshare.com/v2/articles/{article_id}")
            except Exception:
                meta = None
            if isinstance(meta, dict):
                files = [f for f in (meta.get("files") or []) if isinstance(f, dict)]
                for f in files:
                    dl = f.get("download_url")
                    name = str(f.get("name") or "").lower()
                    if isinstance(dl, str) and dl.startswith("https://") and name.endswith(".pdf"):
                        return dl, f"ACS Figshare SI PDF ({si_doi})"
                for f in files:
                    dl = f.get("download_url")
                    if isinstance(dl, str) and dl.startswith("https://"):
                        return dl, f"ACS Figshare SI attachment ({si_doi})"
        return target_url, f"ACS Figshare SI landing ({si_doi})"
    return None


# ---------------------------------------------------------------------------
# Staging helper (strictly under gitignored .temp/fulltext/)
# ---------------------------------------------------------------------------
def _check_no_symlink_components(path: Path, stop_at: Optional[Path] = None) -> None:
    """Raise NotADirectoryError if path or any existing ancestor up to stop_at is a symlink."""
    current = path
    visited: set[Path] = set()
    while current not in visited:
        visited.add(current)
        if current.is_symlink():
            raise NotADirectoryError(f"Symlinked staging path component is not allowed: {current}")
        if stop_at is not None and current == stop_at:
            break
        if current.parent == current:
            break
        current = current.parent


def _validate_staging_destination(
    dest_path: Path,
    *,
    staging_root: Optional[Path] = None,
) -> Path:
    """Validate staging destination path against symlinked roots, escapes, and tracked repo dirs."""
    if "references_cache" in dest_path.parts:
        raise ValueError(
            f"Refusing to write full text into references_cache ({dest_path}). "
            "Stage full text under gitignored .temp/fulltext/ instead."
        )

    if staging_root is not None:
        _check_no_symlink_components(staging_root)
        if staging_root.exists() and not staging_root.is_dir():
            raise NotADirectoryError(f"Staging output root is not a directory: {staging_root}")
        resolved_root = staging_root.resolve(strict=False)
        if "references_cache" in resolved_root.parts:
            raise ValueError(
                f"Refusing to write full text into references_cache ({resolved_root})."
            )
        candidate = dest_path if dest_path.is_absolute() else (staging_root / dest_path)
        if candidate.is_symlink():
            raise ValueError(f"Refusing to overwrite symlinked staging file: {candidate}")
        resolved_dest = candidate.resolve(strict=False)
        if not resolved_dest.is_relative_to(resolved_root) or resolved_dest == resolved_root:
            raise ValueError(
                f"Destination {dest_path} escapes staging output root {staging_root}"
            )
        _check_no_symlink_components(candidate.parent, stop_at=staging_root)
    else:
        _check_no_symlink_components(dest_path.parent)
        if dest_path.is_symlink():
            raise NotADirectoryError(f"Symlinked destination file is not allowed: {dest_path}")
        resolved_dest = dest_path.resolve(strict=False)

    if "references_cache" in resolved_dest.parts:
        raise ValueError(
            f"Refusing to write full text into references_cache ({resolved_dest}). "
            "Stage full text under gitignored .temp/fulltext/ instead."
        )

    if resolved_dest.is_relative_to(REPO_ROOT):
        rel_parts = resolved_dest.relative_to(REPO_ROOT).parts
        if (
            not rel_parts
            or rel_parts[0] in FORBIDDEN_REPO_DIRS
            or rel_parts[:2] != (".temp", "fulltext")
        ):
            raise ValueError(
                f"Refusing to stage full text inside repository path {resolved_dest}; "
                "use .temp/fulltext/ instead."
            )

    return resolved_dest


def _atomic_write_bytes(dest: Path, payload: bytes) -> None:
    """Atomically write payload to dest via a sibling temp file + fsync + os.replace."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    _check_no_symlink_components(dest.parent)
    if dest.is_symlink():
        raise NotADirectoryError(f"Refusing to write through symlink: {dest}")
    fd, tmp_name = tempfile.mkstemp(
        dir=str(dest.parent),
        prefix=f".{dest.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, dest)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def stage_fulltext_for_curation(
    url: str,
    filename: str | Path,
    *,
    output_root: Path = DEFAULT_STAGING_ROOT,
    timeout: int = 30,
) -> tuple[bool, str, Optional[Path]]:
    """
    Download or copy full text strictly inside gitignored `.temp/fulltext/`
    (or an explicit `output_root` during testing).
    Raises `NotADirectoryError` on a symlinked output root and `ValueError`
    on path escape or forbidden destination.
    """
    dest = _validate_staging_destination(Path(filename), staging_root=output_root)
    ok, note = fetch_to_staging(url, dest, timeout=timeout, _validated_dest=dest)
    return ok, note, (dest if ok else None)


def fetch_to_staging(
    url: str,
    dest_path: Path,
    timeout: int = 30,
    *,
    _validated_dest: Optional[Path] = None,
) -> tuple[bool, str]:
    """
    Download `url` (or copy `file://` URL) to `dest_path`.
    Refuses to write inside `references_cache/`, tracked repository directories,
    or symlinked output roots.
    """
    resolved = (
        _validated_dest
        if _validated_dest is not None
        else _validate_staging_destination(dest_path)
    )

    if url.startswith("file://"):
        parsed = urllib.parse.urlsplit(url)
        raw_path = urllib.parse.unquote(parsed.path) if parsed.path else url[len("file://") :]
        src_path = Path(raw_path)
        storage_dir = _zotero_data_dir() / "storage"
        safe_src = _resolve_zotero_storage_pdf(storage_dir, src_path)
        if safe_src is None:
            raise ValueError(
                "Refusing to stage local file outside Zotero storage root or non-regular PDF: "
                f"{src_path}"
            )
        payload = safe_src.read_bytes()
        _atomic_write_bytes(resolved, payload)
        return True, f"Copied local PDF ({len(payload)} bytes)"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,application/xml,text/xml,*/*;q=0.8",
    }
    els_key = os.environ.get("ELSEVIER_API_KEY") or os.environ.get("ELS_API_KEY")
    if "api.elsevier.com" in url and els_key:
        headers["X-ELS-APIKey"] = els_key
    wiley_token = os.environ.get("WILEY_TDM_TOKEN") or os.environ.get("WILEY_TDM_CLIENT_TOKEN")
    if "api.wiley.com" in url and wiley_token:
        headers["Wiley-TDM-Client-Token"] = wiley_token

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            payload = resp.read()
    except Exception as exc:
        return False, f"HTTP fetch failed: {exc}"

    is_pdf = payload.startswith(b"%PDF-")
    is_xml = payload.lstrip().startswith((b"<?xml", b"<article", b"<full-text-retrieval-response"))
    if not (is_pdf or is_xml):
        return (
            False,
            f"Fetched payload is neither PDF nor XML (Content-Type={ctype!r}, "
            f"first_bytes={payload[:32]!r})",
        )

    _atomic_write_bytes(resolved, payload)
    return True, f"Saved {'PDF' if is_pdf else 'XML'} ({len(payload)} bytes)"


# ---------------------------------------------------------------------------
# Ladder orchestrator
# ---------------------------------------------------------------------------
def check_availability(
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    pmcid: Optional[str] = None,
    title: Optional[str] = None,
    stage_dir: Optional[Path] = None,
) -> AccessReport:
    cleaned_doi = _clean_doi(doi) if doi else None
    report = AccessReport(doi=cleaned_doi or doi, pmid=pmid, pmcid=pmcid, title=title)

    # Hydrate identifiers from Europe PMC first
    rec = epmc_core(pmid=pmid, pmcid=pmcid, doi=cleaned_doi)
    if rec:
        report.doi = report.doi or (_clean_doi(rec["doi"]) if rec.get("doi") else None)
        report.pmid = report.pmid or rec.get("pmid")
        report.pmcid = report.pmcid or rec.get("pmcid")
        report.title = report.title or rec.get("title")

    if not report.title and report.doi:
        cr = crossref_meta(report.doi)
        if cr and cr.get("title"):
            report.title = cr["title"][0]
    else:
        cr = None

    # 1. Zotero local storage
    zot = try_zotero_local(doi=report.doi, pmid=report.pmid, title=report.title)
    if zot:
        url, note = zot
        report.attempts.append(AccessAttempt("zotero_local", "found", url, "application/pdf", note))
        report.fulltext_available = True
        report.best_rung = "zotero_local"
        report.best_url = url
    else:
        report.attempts.append(AccessAttempt("zotero_local", "not_found"))

    # 2. Europe PMC
    epmc_hit = try_epmc_fulltext(rec)
    if epmc_hit:
        url, ctype, note = epmc_hit
        report.attempts.append(AccessAttempt("europe_pmc", "found", url, ctype, note))
        if not report.fulltext_available:
            report.fulltext_available = True
            report.best_rung = "europe_pmc"
            report.best_url = url
    else:
        report.attempts.append(AccessAttempt("europe_pmc", "not_found"))

    # 3. OpenAlex OA
    if report.doi:
        oa_hit = try_openalex_oa(report.doi)
        if oa_hit:
            url, note = oa_hit
            report.attempts.append(AccessAttempt("openalex_oa", "found", url, None, note))
            if not report.fulltext_available:
                report.fulltext_available = True
                report.best_rung = "openalex_oa"
                report.best_url = url
        else:
            report.attempts.append(AccessAttempt("openalex_oa", "not_found"))

    # 4. DOE OSTI.gov
    osti_hit = try_osti(doi=report.doi, title=report.title)
    if osti_hit:
        url, note = osti_hit
        report.attempts.append(AccessAttempt("osti_gov", "found", url, None, note))
        if not report.fulltext_available:
            report.fulltext_available = True
            report.best_rung = "osti_gov"
            report.best_url = url
    else:
        report.attempts.append(AccessAttempt("osti_gov", "not_found"))

    # 5. CrossRef TDM / Publisher APIs
    if report.doi:
        tdm_hit = try_crossref_tdm(report.doi, cr_msg=cr)
        if tdm_hit:
            url, note = tdm_hit
            report.attempts.append(AccessAttempt("crossref_tdm", "found", url, None, note))
            if not report.fulltext_available:
                report.fulltext_available = True
                report.best_rung = "crossref_tdm"
                report.best_url = url
        else:
            report.attempts.append(AccessAttempt("crossref_tdm", "not_found"))

    # 6. LBNL / UC Library
    if report.doi:
        lbnl_hit = try_lbnl_library(report.doi)
        if lbnl_hit:
            url, note = lbnl_hit
            report.attempts.append(AccessAttempt("lbnl_library", "found", url, None, note))
            if not report.fulltext_available:
                report.fulltext_available = True
                report.best_rung = "lbnl_library"
                report.best_url = url
        else:
            has_lbnl_env = bool(
                (os.environ.get("LBNL_LIBKEY_ID") and os.environ.get("LBNL_LIBKEY_TOKEN"))
                or os.environ.get("LBNL_PROXY_PREFIX")
            )
            report.attempts.append(
                AccessAttempt(
                    "lbnl_library",
                    "not_found" if has_lbnl_env else "skipped",
                    note=(
                        None
                        if has_lbnl_env
                        else "Set LBNL_LIBKEY_ID+LBNL_LIBKEY_TOKEN or LBNL_PROXY_PREFIX"
                    ),
                )
            )

    # 7. CORE API v3
    core_hit = try_core(doi=report.doi, title=report.title)
    if core_hit:
        url, note = core_hit
        report.attempts.append(AccessAttempt("core_v3", "found", url, None, note))
        if not report.fulltext_available:
            report.fulltext_available = True
            report.best_rung = "core_v3"
            report.best_url = url
    else:
        has_core = bool((os.environ.get("CORE_API_KEY") or "").strip())
        report.attempts.append(
            AccessAttempt(
                "core_v3",
                "not_found" if has_core else "skipped",
                note=None if has_core else "Set CORE_API_KEY for CORE repository lookup",
            )
        )

    # 8. Semantic Scholar
    s2_hit = try_semantic_scholar(doi=report.doi, pmid=report.pmid)
    if s2_hit:
        url, note = s2_hit
        report.attempts.append(AccessAttempt("semantic_scholar", "found", url, None, note))
        if not report.fulltext_available:
            report.fulltext_available = True
            report.best_rung = "semantic_scholar"
            report.best_url = url
    else:
        report.attempts.append(AccessAttempt("semantic_scholar", "not_found"))

    # 9. ACS Figshare Supporting Information
    if report.doi and report.doi.startswith("10.1021/"):
        acs_hit = try_acs_figshare_si(report.doi)
        if acs_hit:
            url, note = acs_hit
            report.attempts.append(AccessAttempt("acs_figshare_si", "found", url, None, note))
            if not report.fulltext_available:
                report.fulltext_available = True
                report.best_rung = "acs_figshare_si"
                report.best_url = url
        else:
            report.attempts.append(AccessAttempt("acs_figshare_si", "not_found"))

    # Optional staging into .temp/fulltext/
    if stage_dir and report.fulltext_available and report.best_url:
        safe_id = re.sub(
            r"[^A-Za-z0-9._-]+", "_", report.doi or report.pmid or report.pmcid or "paper"
        )
        ext = ".xml" if "fullTextXML" in report.best_url or "text/xml" in report.best_url else ".pdf"
        ok, msg, dest = stage_fulltext_for_curation(
            report.best_url,
            f"{safe_id}{ext}",
            output_root=stage_dir,
        )
        if ok and dest is not None:
            report.local_staged_path = str(dest)
        else:
            report.attempts.append(AccessAttempt("stage_download", "error", report.best_url, note=msg))

    if not report.fulltext_available:
        doi_str = report.doi or "<DOI>"
        report.manual_fallback_instructions = [
            "Option A (Zotero Connector): Open https://doi.org/"
            f"{doi_str} in your browser while on LBNL VPN / UC library proxy "
            "and click the Zotero Connector 'Save to Zotero' button (with PDF attachment); "
            "re-run fulltext_access.py and Rung 1 (zotero_local) will pick it up automatically.",
            "Option B (Elsevier / Wiley TDM API key): Export ELSEVIER_API_KEY (from dev.elsevier.com, "
            "free for academic subscribers) or WILEY_TDM_TOKEN and re-run.",
            "Option C (Stage PDF manually): Save the PDF to "
            f".temp/fulltext/{re.sub(r'[^A-Za-z0-9._-]+', '_', doi_str)}.pdf "
            "(gitignored; never commit full text).",
        ]

    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check legal full-text availability across Zotero, OA, OSTI, TDM, and LBNL rungs."
    )
    ap.add_argument("--doi", help="Article DOI")
    ap.add_argument("--pmid", help="PubMed ID")
    ap.add_argument("--pmcid", help="PubMed Central ID (e.g. PMC1234567)")
    ap.add_argument("--title", help="Article title (optional fallback)")
    ap.add_argument(
        "--stage",
        action="store_true",
        help="Download best full text into gitignored .temp/fulltext/",
    )
    ap.add_argument(
        "--stage-dir",
        type=Path,
        default=DEFAULT_STAGING_ROOT,
        help="Staging directory (default: .temp/fulltext)",
    )
    args = ap.parse_args()

    if not any([args.doi, args.pmid, args.pmcid, args.title]):
        ap.error("Provide at least one of --doi, --pmid, --pmcid, or --title")

    report = check_availability(
        doi=args.doi,
        pmid=args.pmid,
        pmcid=args.pmcid,
        title=args.title,
        stage_dir=args.stage_dir if args.stage else None,
    )
    print(json.dumps(asdict(report), indent=2))
    return 0 if report.fulltext_available else 2


if __name__ == "__main__":
    sys.exit(main())
