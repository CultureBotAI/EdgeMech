"""Issue #100: exercise actual urllib redirect dispatch without external requests."""

from __future__ import annotations

import io
import sys
import urllib.request
import urllib.response
from email.message import Message
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import fulltext_access as fa  # noqa: E402

PDF = b"%PDF-1.5 synthetic full-text fixture"


class ScriptedHTTP(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    """All responses use the real opener's redirect and HTTP-error machinery."""

    def __init__(self, responses):
        super().__init__()
        self.responses = iter(responses)
        self.calls = []

    def http_open(self, req):
        self.calls.append((req.full_url, {key.lower(): value for key, value in req.header_items()}))
        code, location, payload = next(self.responses)
        headers = Message()
        headers["Content-Type"] = "application/pdf"
        if location:
            headers["Location"] = location
        response = urllib.response.addinfourl(io.BytesIO(payload), headers, req.full_url, code)
        response.msg = "Synthetic response"
        return response

    https_open = http_open


def wire_transport(monkeypatch, responses):
    transport = ScriptedHTTP(responses)
    opener = urllib.request.build_opener(fa._SafeRedirectHandler(), transport)
    monkeypatch.setattr(fa.urllib.request, "build_opener", lambda *args: opener)
    monkeypatch.setenv("WILEY_TDM_TOKEN", "synthetic-wiley")
    monkeypatch.setenv("ELSEVIER_API_KEY", "synthetic-elsevier")
    return transport


@pytest.mark.parametrize("url", [
    "https://example.invalid/?next=api.wiley.com",
    "https://example.invalid/api.elsevier.com/paper",
    "https://api.wiley.com.example.invalid/paper",
    "https://api.elsevier.com.example.invalid/paper",
    "http://api.wiley.com/paper",
    "https://api.wiley.com./paper",
])
def test_deceptive_or_insecure_origins_never_receive_provider_credentials(tmp_path, monkeypatch, url):
    transport = wire_transport(monkeypatch, [(200, None, PDF)])
    dest = tmp_path / "paper.pdf"
    assert fa.fetch_to_staging(url, dest)[0]
    assert dest.read_bytes() == PDF
    assert "wiley-tdm-client-token" not in transport.calls[0][1]
    assert "x-els-apikey" not in transport.calls[0][1]


@pytest.mark.parametrize("url", [
    "https://api.wiley.com:444/paper", "https://user:pass@api.wiley.com/paper",
    "https://api.wiley.com@other.invalid/paper", "https://api.elsevier.com:bad/paper",
    "https://api.wiley.com\\other.invalid/paper", "https://api.wiley.com/\npaper",
])
def test_ambiguous_initial_origins_are_refused_before_network(tmp_path, monkeypatch, url):
    transport = wire_transport(monkeypatch, [])
    dest = tmp_path / "paper.pdf"
    assert not fa.fetch_to_staging(url, dest)[0]
    assert transport.calls == []
    assert not dest.exists()


@pytest.mark.parametrize(("url", "header", "value"), [
    ("https://api.wiley.com/paper", "wiley-tdm-client-token", "synthetic-wiley"),
    ("https://api.elsevier.com:443/paper", "x-els-apikey", "synthetic-elsevier"),
])
def test_exact_provider_origin_receives_only_its_credential(tmp_path, monkeypatch, url, header, value):
    transport = wire_transport(monkeypatch, [(302, "/next", b""), (200, None, PDF)])
    assert fa.fetch_to_staging(url, tmp_path / "paper.pdf")[0]
    for _, headers in transport.calls:
        assert headers[header] == value
        assert sum(key in headers for key in ("x-els-apikey", "wiley-tdm-client-token")) == 1


def test_wiley_binary_redirect_strips_token_and_does_not_restore_it(tmp_path, monkeypatch):
    transport = wire_transport(monkeypatch, [
        (302, "https://alm.wiley.com/binary/paper", b""),
        (302, "https://api.wiley.com/public-paper", b""), (200, None, PDF),
    ])
    dest = tmp_path / "paper.pdf"
    assert fa.fetch_to_staging("https://api.wiley.com/paper", dest)[0]
    assert dest.read_bytes() == PDF
    assert transport.calls[0][1]["wiley-tdm-client-token"] == "synthetic-wiley"
    for _, headers in transport.calls[1:]:
        assert "wiley-tdm-client-token" not in headers
        assert "x-els-apikey" not in headers


@pytest.mark.parametrize("location", [
    "http://alm.wiley.com/paper", "https://user:pass@alm.wiley.com/paper",
    "https://alm.wiley.com:444/paper", "file:///private/paper.pdf",
])
def test_unsafe_redirects_are_refused_before_followup(tmp_path, monkeypatch, location):
    transport = wire_transport(monkeypatch, [(302, location, b"")])
    dest = tmp_path / "paper.pdf"
    ok, note = fa.fetch_to_staging("https://api.wiley.com/paper", dest)
    assert not ok
    assert len(transport.calls) == 1
    assert not dest.exists()
    assert "pass" not in note


def test_anonymous_oa_redirects_and_http_upgrade_work(tmp_path, monkeypatch):
    transport = wire_transport(monkeypatch, [
        (302, "https://repository.example.invalid/paper", b""),
        (302, "https://binary.example.invalid/paper.pdf", b""), (200, None, PDF),
    ])
    dest = tmp_path / "paper.pdf"
    assert fa.fetch_to_staging("http://repository.example.invalid/start", dest)[0]
    assert len(transport.calls) == 3
    assert dest.read_bytes() == PDF


def test_foreign_host_rejection_is_not_saved_as_fulltext(tmp_path, monkeypatch):
    transport = wire_transport(monkeypatch, [
        (302, "https://alm.wiley.com/paper", b""), (403, None, b"Forbidden"),
    ])
    dest = tmp_path / "paper.pdf"
    ok, note = fa.fetch_to_staging("https://api.wiley.com/paper", dest)
    assert not ok and "403" in note
    assert not dest.exists()
    assert "wiley-tdm-client-token" not in transport.calls[1][1]


def test_redirect_chain_is_bounded(tmp_path, monkeypatch):
    transport = wire_transport(monkeypatch, [
        (302, f"https://api.wiley.com/next-{number}", b"") for number in range(20)
    ])
    assert not fa.fetch_to_staging("https://api.wiley.com/start", tmp_path / "paper.pdf")[0]
    assert len(transport.calls) <= 7


def test_json_bearer_credentials_are_also_stripped_on_foreign_redirect(monkeypatch):
    transport = wire_transport(monkeypatch, [
        (302, "https://other.example.invalid/catalog", b""), (200, None, b'{"ok": true}'),
    ])
    assert fa._http_get_json("https://api.core.ac.uk/catalog", {
        "Authorization": "Bearer synthetic-core", "Cookie": "synthetic-cookie",
        "X-Custom-Credential": "synthetic-other",
    }) == {"ok": True}
    assert transport.calls[0][1]["authorization"] == "Bearer synthetic-core"
    for name in ("authorization", "cookie", "x-custom-credential"):
        assert name not in transport.calls[1][1]
