"""Issue #108: paper-helper reruns must preserve retained evidence byte for byte."""

import importlib.util
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/adhoc/inspect_edge47_paper_20261115.py"


@pytest.mark.parametrize("mode,change", [
    ("url", "artifact"), ("url", "receipt"),
    ("xml", "artifact"), ("xml", "receipt"),
    ("pdf", "artifact"), ("pdf", "info"), ("pdf", "receipt"),
    ("search", "receipt"),
])
def test_cli_rerun_preserves_artifacts_and_receipts(tmp_path, monkeypatch, mode, change):
    spec = importlib.util.spec_from_file_location("edge47_paper_under_test", SCRIPT)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    output = tmp_path / ".temp" / "evidence"
    source = tmp_path / "source"
    state = {"raw": b"original image", "content_type": "image/jpeg",
             "text": b"Original text\f", "info": b"Pages: 1\n", "hit": None}
    if mode == "url":
        def open_response(*args, **kwargs):
            response = io.BytesIO(state["raw"])
            response.headers = {"Content-Type": state["content_type"]}
            return response

        monkeypatch.setattr(helper, "build_opener", lambda *args: SimpleNamespace(open=open_response))
        arguments = ["--url", "https://cdn.ncbi.nlm.nih.gov/fixture.jpg",
                     "--artifact-name", "figure.jpg"]
        expected = {"figure.jpg", "figure.jpg.receipt.json"}
    elif mode == "xml":
        source.write_bytes(b'<article><front><article-meta><article-id pub-id-type="doi">'
                           b'10.1/fixture</article-id><title-group><article-title>Fixture'
                           b'</article-title></title-group></article-meta></front><body>'
                           b'<sec id="s1"><title>Results</title><p>Original text</p></sec>'
                           b'</body></article>')
        arguments = ["--xml", str(source)]
        expected = {"paper-sections.json", "xml-extraction-receipt.json"}
    elif mode == "pdf":
        source.write_bytes(b"%PDF-fixture-original")

        def convert(command, *, check, capture_output):
            assert check and capture_output
            if command[0] == "pdftotext":
                # The converter must write only to stdout, never a retained file.
                assert command == ["pdftotext", "-layout", str(source), "-"]
                return SimpleNamespace(stdout=state["text"])
            assert command == ["pdfinfo", str(source)]
            return SimpleNamespace(stdout=state["info"])

        monkeypatch.setattr(helper.subprocess, "run", convert)
        arguments = ["--paper", str(source)]
        expected = {"paper-layout.txt", "paper-info.txt", "extraction-receipt.json"}
    else:
        fake_module = SimpleNamespace(try_zotero_local=lambda **kwargs: state["hit"])
        fake_spec = SimpleNamespace(name="edge47_safe_fulltext",
                                    loader=SimpleNamespace(exec_module=lambda module: None))
        monkeypatch.setattr(helper.importlib.util, "spec_from_file_location",
                            lambda *args: fake_spec)
        monkeypatch.setattr(helper.importlib.util, "module_from_spec", lambda spec: fake_module)
        monkeypatch.setitem(sys.modules, fake_spec.name, fake_module)
        arguments = ["--safe-fulltext-module", str(tmp_path / "mock-module.py")]
        expected = {"local-search.json"}
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output-dir", str(output), *arguments])

    def snapshot():
        return {path.name: path.read_bytes() for path in output.iterdir()}

    helper.main()
    retained = snapshot()
    assert set(retained) == expected
    assert all(retained.values())
    helper.main()
    assert snapshot() == retained

    if mode == "url":
        state["raw" if change == "artifact" else "content_type"] = (
            b"changed image" if change == "artifact" else "image/png")
    elif mode == "xml":
        raw = source.read_bytes()
        source.write_bytes(raw.replace(b"Original text", b"Changed text") if change == "artifact"
                           else raw + b"<!-- changed source, same extracted text -->")
    elif mode == "pdf":
        if change == "receipt":
            source.write_bytes(b"%PDF-fixture-changed")
        else:
            state["text" if change == "artifact" else "info"] = b"Changed converter output"
    else:
        state["hit"] = {"path": "new-local-result.pdf"}

    with pytest.raises(ValueError, match="refusing to replace different retained evidence"):
        helper.main()
    assert snapshot() == retained
