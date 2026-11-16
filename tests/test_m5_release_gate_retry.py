"""Keep durable gate scratch outside ephemeral filesystem roots, including aliases."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def retry():
    """Load only the retry boundary helper, without creating an environment record."""
    path = Path(__file__).parents[1] / "scripts/adhoc/m5_release_gate_retry_20261116.py"
    spec = importlib.util.spec_from_file_location("m5_gate_retry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["/tmp", "/private/tmp", "/private/var/folders"])
def test_exact_existing_ephemeral_roots_are_refused_without_writing_them(retry, name):
    """The root itself must be rejected, not just strings containing its trailing slash."""
    path = Path(name)
    if not path.exists():
        pytest.skip("Platform does not have this temporary root")
    with pytest.raises(ValueError, match="durable"):
        retry.durable_scratch(path)


def test_durable_named_alias_to_temporary_root_cannot_pass(retry, tmp_path):
    """A durable-looking name does not change the resolved storage lifetime."""
    alias = tmp_path / "durable-gate-scratch"
    alias.symlink_to(Path("/tmp"), target_is_directory=True)
    with pytest.raises(ValueError, match="durable"):
        retry.durable_scratch(alias)


def test_actual_durable_directory_remains_usable(retry):
    """The boundary repair accepts task-owned durable scratch and does not require /tmp."""
    # Read only an existing directory; pytest itself may place tmp_path in /tmp.
    scratch = Path(__file__).resolve().parent
    ephemeral = (Path("/tmp").resolve(), Path("/private/tmp"), Path("/private/var/folders"))
    if any(scratch.is_relative_to(root) for root in ephemeral):
        pytest.skip("Checkout itself is in ephemeral storage")
    assert retry.durable_scratch(scratch) == scratch
