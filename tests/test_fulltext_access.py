"""Unit tests for scripts/fulltext_access.py legal full-text access ladder."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import fulltext_access as fa  # noqa: E402


def test_user_agent_has_no_email_or_at_sign():
    """Standing agreement: never disclose an email address or @-token in User-Agent."""
    assert "@" not in fa.USER_AGENT
    assert "mailto" not in fa.USER_AGENT.lower()


def test_clean_doi():
    assert fa._clean_doi("https://doi.org/10.1016/S0021-9258(19)41496-8") == (
        "10.1016/S0021-9258(19)41496-8"
    )
    assert fa._clean_doi("http://dx.doi.org/10.1007/BF00408017") == "10.1007/BF00408017"
    assert fa._clean_doi("HTTPS://DOI.ORG/10.1038/nature01") == "10.1038/nature01"
    assert fa._clean_doi("DOI:10.1128/JB.00123-10") == "10.1128/JB.00123-10"
    assert fa._clean_doi("  doi:10.1128/JB.00123-10  ") == "10.1128/JB.00123-10"


def test_epmc_core_and_crossref_meta_normalize_doi_urls(monkeypatch):
    captured_urls: list[str] = []

    def fake_get_json(url: str, headers=None, timeout: int = 15):
        captured_urls.append(url)
        return {"resultList": {"result": []}, "message": {"title": ["Normalized"]}}

    monkeypatch.setattr(fa, "_http_get_json", fake_get_json)
    fa.epmc_core(doi="HTTPS://DX.DOI.ORG/10.1016/j.cell.2020.01.001")
    fa.crossref_meta("http://dx.doi.org/10.1016/j.cell.2020.01.001")
    assert len(captured_urls) == 2
    assert "https%3a" not in captured_urls[0].lower()
    assert "DOI%3A%2210.1016/j.cell.2020.01.001%22" in captured_urls[0]
    assert captured_urls[1] == "https://api.crossref.org/works/10.1016%2Fj.cell.2020.01.001"


def test_try_core_normalizes_doi_strips_key_and_escapes_quotes(monkeypatch):
    captured: list[tuple[str, dict | None]] = []

    def fake_get_json(url: str, headers=None, timeout: int = 15):
        captured.append((url, headers))
        return {"results": [{"downloadUrl": "https://core.ac.uk/download/pdf/123.pdf"}]}

    monkeypatch.setenv("CORE_API_KEY", "  secret-token  ")
    monkeypatch.setattr(fa, "_http_get_json", fake_get_json)

    hit = fa.try_core(doi="https://doi.org/10.1000/a\"b\\c")
    assert hit is not None
    url, _ = hit
    assert url == "https://core.ac.uk/download/pdf/123.pdf"
    req_url, req_headers = captured[0]
    assert req_headers == {"Authorization": "Bearer secret-token"}
    decoded_query = fa.urllib.parse.unquote(req_url)
    assert 'doi:"10.1000/a\\"b\\\\c"' in decoded_query


def _init_zotero_db(db_path: Path, att_key: str, att_path: str, doi_value: str) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER);
        CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT);
        CREATE TABLE itemAttachments (
            itemID INTEGER PRIMARY KEY,
            parentItemID INTEGER,
            path TEXT,
            contentType TEXT
        );
        """
    )
    conn.execute("INSERT INTO fields VALUES (1, 'DOI');")
    conn.execute("INSERT INTO itemDataValues VALUES (10, ?);", (doi_value,))
    conn.execute("INSERT INTO itemData VALUES (100, 1, 10);")
    conn.execute("INSERT INTO items VALUES (100, 'PARENT01');")
    conn.execute("INSERT INTO items VALUES (200, ?);", (att_key,))
    conn.execute(
        "INSERT INTO itemAttachments VALUES (200, 100, ?, 'application/pdf');",
        (att_path,),
    )
    conn.commit()
    conn.close()


def test_try_zotero_local_finds_pdf_by_doi(tmp_path, monkeypatch):
    """Verify Rung 1 (Zotero local SQLite + storage directory) resolves local PDFs."""
    zotero_dir = tmp_path / "Zotero"
    storage_dir = zotero_dir / "storage" / "ABCD1234"
    storage_dir.mkdir(parents=True)
    pdf_path = storage_dir / "Markarian_1975.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf content")

    db_path = zotero_dir / "zotero.sqlite"
    _init_zotero_db(
        db_path,
        "ABCD1234",
        "storage:Markarian_1975.pdf",
        "10.1016/S0021-9258(19)41496-8",
    )

    monkeypatch.setenv("ZOTERO_DATA_DIR", str(zotero_dir))
    hit = fa.try_zotero_local(doi="https://doi.org/10.1016/S0021-9258(19)41496-8")
    assert hit is not None
    url, note = hit
    assert url == f"file://{pdf_path.resolve()}"
    assert "ABCD1234" in note


def test_try_zotero_local_rejects_external_traversal_and_symlink_paths(tmp_path, monkeypatch):
    """Issue #27: reject non-storage: paths, .. traversal, and symlink escapes in Zotero."""
    zotero_dir = tmp_path / "Zotero"
    storage_dir = zotero_dir / "storage" / "ABCD1234"
    storage_dir.mkdir(parents=True)
    outside_pdf = tmp_path / "outside.pdf"
    outside_pdf.write_bytes(b"%PDF-1.4 outside")

    db_path = zotero_dir / "zotero.sqlite"
    monkeypatch.setenv("ZOTERO_DATA_DIR", str(zotero_dir))

    # 1. Absolute path without storage: prefix must be rejected
    _init_zotero_db(db_path, "ABCD1234", str(outside_pdf), "10.1000/ext")
    assert fa.try_zotero_local(doi="10.1000/ext") is None

    # 2. Relative .. traversal escaping storage_dir must be rejected
    db_path.unlink()
    _init_zotero_db(db_path, "ABCD1234", "storage:../../outside.pdf", "10.1000/trav")
    assert fa.try_zotero_local(doi="10.1000/trav") is None

    # 3. Symlinked PDF inside storage/<key>/ pointing outside must be rejected
    db_path.unlink()
    symlink_pdf = storage_dir / "linked.pdf"
    symlink_pdf.symlink_to(outside_pdf)
    _init_zotero_db(db_path, "ABCD1234", "storage:linked.pdf", "10.1000/sym")
    assert fa.try_zotero_local(doi="10.1000/sym") is None

    # 4. fetch_to_staging must also reject file:// outside ZOTERO_DATA_DIR/storage
    dest = tmp_path / ".temp" / "fulltext" / "out.pdf"
    with pytest.raises(ValueError, match="Zotero storage root"):
        fa.fetch_to_staging(f"file://{outside_pdf}", dest)


def test_try_epmc_fulltext_prefers_xml_when_oa():
    rec = {
        "pmcid": "PMC1234567",
        "isOpenAccess": "Y",
        "inEPMC": "Y",
    }
    hit = fa.try_epmc_fulltext(rec)
    assert hit is not None
    url, ctype, note = hit
    assert url == "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1234567/fullTextXML"
    assert ctype == "application/xml"
    assert "PMC1234567" in note


def test_try_openalex_oa_extracts_best_pdf(monkeypatch):
    def fake_get_json(url: str, headers=None, timeout: int = 15):
        assert "api.openalex.org/works/" in url
        return {
            "best_oa_location": {
                "pdf_url": "https://escholarship.org/content/qt123/qt123.pdf",
                "host_type": "repository",
            }
        }

    monkeypatch.setattr(fa, "_http_get_json", fake_get_json)
    hit = fa.try_openalex_oa("10.1016/S0021-9258(19)41496-8")
    assert hit is not None
    url, note = hit
    assert url == "https://escholarship.org/content/qt123/qt123.pdf"
    assert "repository" in note


def test_try_osti_finds_doe_record(monkeypatch):
    def fake_get_json(url: str, headers=None, timeout: int = 15):
        assert "osti.gov/api/v1/records" in url
        return [
            {
                "osti_id": "1999999",
                "links": [
                    {"rel": "fulltext", "href": "https://www.osti.gov/servlets/purl/1999999"}
                ],
            }
        ]

    monkeypatch.setattr(fa, "_http_get_json", fake_get_json)
    hit = fa.try_osti(doi="10.1038/s41564-023-01345-x")
    assert hit is not None
    url, note = hit
    assert url == "https://www.osti.gov/servlets/purl/1999999"
    assert "1999999" in note


def test_try_crossref_tdm_skips_elsevier_without_key_and_uses_with_key(monkeypatch):
    cr_msg = {
        "link": [
            {
                "URL": "https://api.elsevier.com/content/article/PII:S0021925819414968?httpAccept=text/xml",
                "content-type": "text/xml",
                "intended-application": "text-mining",
            }
        ]
    }
    monkeypatch.delenv("ELSEVIER_API_KEY", raising=False)
    monkeypatch.delenv("ELS_API_KEY", raising=False)
    assert fa.try_crossref_tdm("10.1016/S0021-9258(19)41496-8", cr_msg=cr_msg) is None

    monkeypatch.setenv("ELSEVIER_API_KEY", "dummy-key")
    hit = fa.try_crossref_tdm("10.1016/S0021-9258(19)41496-8", cr_msg=cr_msg)
    assert hit is not None
    url, note = hit
    assert "api.elsevier.com/content/article/doi/" in url
    assert "ELSEVIER_API_KEY" in note


def test_try_lbnl_library_proxy_prefix(monkeypatch):
    monkeypatch.delenv("LBNL_LIBKEY_ID", raising=False)
    monkeypatch.delenv("LBNL_LIBKEY_TOKEN", raising=False)
    monkeypatch.setenv("LBNL_PROXY_PREFIX", "https://ezproxy.lbl.gov/login?url=")
    hit = fa.try_lbnl_library("10.1007/BF00408017")
    assert hit is not None
    url, note = hit
    assert url == "https://ezproxy.lbl.gov/login?url=/https://doi.org/10.1007/BF00408017"
    assert "LBNL_PROXY_PREFIX" in note


def test_fetch_to_staging_blocks_references_cache(tmp_path):
    bad_dest = tmp_path / "references_cache" / "pdfs" / "10.1038_test.pdf"
    with pytest.raises(ValueError, match="references_cache"):
        fa.fetch_to_staging("https://example.org/paper.pdf", bad_dest)


def test_stage_fulltext_for_curation_guards_symlink_root_and_path_escape(tmp_path):
    """Issue #28: stage_fulltext_for_curation rejects symlinked output roots and path escapes."""
    real_root = tmp_path / "real_root"
    real_root.mkdir()
    symlink_root = tmp_path / "symlink_root"
    symlink_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(NotADirectoryError, match="Symlinked"):
        fa.stage_fulltext_for_curation(
            "https://example.org/paper.pdf",
            "paper.pdf",
            output_root=symlink_root,
        )

    staging_root = tmp_path / ".temp" / "fulltext"
    staging_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="escapes staging output root"):
        fa.stage_fulltext_for_curation(
            "https://example.org/paper.pdf",
            "../escaped.pdf",
            output_root=staging_root,
        )

    # Also reject staging inside tracked repo paths such as REPO_ROOT / "src" / "bad.pdf"
    with pytest.raises(ValueError, match="use .temp/fulltext/"):
        fa.fetch_to_staging("https://example.org/paper.pdf", fa.REPO_ROOT / "src" / "bad.pdf")


def test_fetch_to_staging_writes_pdf_to_temp(tmp_path, monkeypatch):
    class FakeResp:
        headers = {"Content-Type": "application/pdf"}

        def read(self):
            return b"%PDF-1.5 fake pdf payload"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(fa.urllib.request, "urlopen", lambda req, timeout=30: FakeResp())
    dest = tmp_path / ".temp" / "fulltext" / "10.1038_test.pdf"
    ok, msg = fa.fetch_to_staging("https://example.org/paper.pdf", dest)
    assert ok is True
    assert dest.exists()
    assert dest.read_bytes().startswith(b"%PDF-1.5")
    assert "Saved PDF" in msg

    # Verify stage_fulltext_for_curation end-to-end
    ok2, msg2, staged = fa.stage_fulltext_for_curation(
        "https://example.org/paper.pdf",
        "10.1038_staged.pdf",
        output_root=tmp_path / ".temp" / "fulltext",
    )
    assert ok2 is True
    assert staged == tmp_path / ".temp" / "fulltext" / "10.1038_staged.pdf"
    assert staged.read_bytes().startswith(b"%PDF-1.5")
    assert "Saved PDF" in msg2


def test_try_acs_figshare_si_resolves_handle(monkeypatch):
    def fake_get_json(url: str, headers=None, timeout: int = 15):
        if "doi.org/api/handles/10.1021/acssynbio.5b00123.s001" in url:
            return {
                "responseCode": 1,
                "values": [
                    {
                        "type": "URL",
                        "data": {
                            "value": (
                                "https://figshare.com/articles/journal_contribution/"
                                "Supporting_Information/12345678"
                            )
                        },
                    }
                ],
            }
        if "api.figshare.com/v2/articles/12345678" in url:
            return {
                "files": [
                    {
                        "name": "sb5b00123_si_002.xlsx",
                        "download_url": "https://ndownloader.figshare.com/files/99999998",
                    },
                    {
                        "name": "sb5b00123_si_001.pdf",
                        "download_url": "https://ndownloader.figshare.com/files/99999999",
                    },
                ]
            }
        return {}

    monkeypatch.setattr(fa, "_http_get_json", fake_get_json)
    assert fa.try_acs_figshare_si("10.1038/s41586-024-00001-1") is None
    hit = fa.try_acs_figshare_si("https://doi.org/10.1021/acssynbio.5b00123")
    assert hit is not None
    assert hit[0] == "https://ndownloader.figshare.com/files/99999999"
    hit_si = fa.try_acs_figshare_si("10.1021/acssynbio.5b00123.s001")
    assert hit_si is not None
    assert hit_si[0] == "https://ndownloader.figshare.com/files/99999999"

