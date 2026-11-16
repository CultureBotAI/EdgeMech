"""Keep canonical release units exclusive and reject scoped or tampered completion evidence."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

HELPER = Path(__file__).resolve().parents[1] / "scripts/adhoc/m5_release_chain_20261116.py"


@pytest.fixture
def chain(tmp_path):
    """Use an isolated output root and restore process permissions after direct launcher calls."""
    spec = importlib.util.spec_from_file_location("m5_release_chain", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def identity(path):
        raw = path.read_bytes()
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    root = tmp_path.resolve()
    launcher = SimpleNamespace(ROOT=root, require=require, identity=identity, safe_path=lambda p: p)
    previous = os.umask(0o077)
    os.umask(previous)
    try:
        yield module, launcher, root
    finally:
        os.umask(previous)


def test_existing_canonical_source_is_refused_before_producer(chain):
    """Even an empty source directory belongs to prior work and cannot be reused implicitly."""
    module, launcher, root = chain
    existing = root / "data/transformed/ontologies"
    existing.mkdir(parents=True)
    sentinel = existing / "retained.tsv"
    sentinel.write_text("previous source evidence\n")
    launcher.prepare = lambda args: {"environment": {"ROBOT_JAVA_ARGS": "", "_JAVA_OPTIONS": ""}}
    args = SimpleNamespace(kg_root=root, source="ontologies")
    with pytest.raises(ValueError, match="Canonical source output already exists"):
        module.prepare(args, launcher)
    assert sentinel.read_text() == "previous source evidence\n"


@pytest.mark.parametrize("damage", ["scoped_only", "changed_member"])
def test_cli_success_cannot_certify_incomplete_or_changed_source(chain, damage):
    """A zero exit code with a scoped record or edited TSV never supplies whole-source evidence."""
    module, launcher, root = chain
    source = root / "data/transformed/ontologies"
    receipt_path = root / "chain.json"
    plan = {
        "canonical_output_base": str(source.parent),
        "canonical_source_directory": str(source),
        "upstream_before": {},
        "ancillary_before": {name: {} for name in module.ANCILLARY},
        "chain_receipt": str(receipt_path),
    }

    def produced(_):
        source.mkdir(parents=True)
        nodes = source / "ro_nodes.tsv"
        nodes.write_text("id\tcategory\n")
        audit = source / "audit.tsv"
        audit.write_text("record\n")
        report = {
            "members": {nodes.name: launcher.identity(nodes)},
            "audit_members": {audit.name: launcher.identity(audit)},
        }
        filename = (
            "ro_source_finalization.json" if damage == "scoped_only" else "source_finalization.json"
        )
        (source / filename).write_text(json.dumps(report))
        (source / "source_fingerprint.json").write_text('{"version": 3}\n')
        if damage == "changed_member":
            nodes.write_text("id\tcategory\nchanged:1\tbiolink:NamedThing\n")
        return 0

    launcher.run = produced
    message = (
        "CLI success lacks actual completion evidence"
        if damage == "scoped_only"
        else "Finalizer member changed"
    )
    with pytest.raises(ValueError, match=message):
        module.run(plan, launcher)
    assert not receipt_path.exists()
