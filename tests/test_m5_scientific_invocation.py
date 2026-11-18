"""Future scientific launch coherence is independent of engineering readiness (#203)."""
from __future__ import annotations

import copy
import shutil
import sys
from pathlib import Path

import pytest
from test_calibration_round import round_inputs as round_inputs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/adhoc"))
import scientific_invocation_20261117 as invocation  # noqa: E402


@pytest.fixture
def contract(round_inputs, monkeypatch):
    rounds, root, _, _, config, put = round_inputs
    monkeypatch.setattr(invocation, "rounds", rounds)
    original_put = put

    def put(path, value):
        target = root / path
        if target.is_file():
            target.chmod(0o600)
        original_put(path, value)

    put("instructions.md", {"schema": invocation.TEMPLATE_SCHEMA,
                            "text": "Use {{manifest_path}} and write under {{output_root}}."})
    config["package_purpose"] = invocation.PURPOSE
    for item in config["files"]:
        if item["role"] in {"instructions", "authority", "evidence", "view"}:
            item["visibility"] = "reviewer"
    helper = root / invocation.HELPER
    helper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / invocation.HELPER, helper)
    config["files"].append({"path": invocation.HELPER, "role": "proof_adapter"})
    session = {"reviewer_id": "reviewer-a", "workdir": str(root),
               "session_root": str(root / ".temp/future-reviewer-a"),
               "output_root": str(root / ".temp/future-reviewer-a/worker")}
    plan = {"schema": invocation.PLAN_SCHEMA, "purpose": invocation.PURPOSE,
            "round_id": config["round_id"], "manifest_path": "future-manifest.json",
            "phase": "blinded_initial_review", "sessions": [session],
            "instruction_paths": ["instructions.md"],
            "read_paths": [rounds.PROTOCOL, *[item["path"] for item in config["files"]
                                            if item.get("visibility") == "reviewer"]]}
    put("instruction-plan.json", plan)
    config["files"].append({"path": "instruction-plan.json", "role": "scientific_instructions"})
    put("future-config.json", config)
    rounds.freeze(root, "future-config.json", "future-manifest.json")
    plan, manifest, bindings = invocation.checked_plan(
        root, "future-manifest.json", "instruction-plan.json")
    put("production/receipt.json", {"fixture": "readiness is not scientific authorization"})
    value = {"schema": invocation.SCHEMA, "purpose": invocation.PURPOSE,
             "round_id": config["round_id"], **bindings, "runtime": {"git_head": "a" * 40},
             "production_receipt": invocation.pin(root, "production/receipt.json"),
             "session": session}
    prompt = invocation.generated_prompt(plan, manifest, session, bindings,
                                          invocation.instruction_templates(root, plan))
    (root / "generated.prompt.md").write_bytes(prompt)
    value["prompt"] = invocation.pin(root, "generated.prompt.md")
    put("invocation.json", value)
    kwargs = {"manifest_path": "future-manifest.json", "runtime": value["runtime"],
              "receipt_path": root / "production/receipt.json",
              "output": Path(session["output_root"]), "prompt": root / "generated.prompt.md"}
    return root, plan, manifest, value, kwargs, put


def test_verified_structured_prompt_and_session_are_bound_and_exclusive(contract):
    root, plan, manifest, value, kwargs, _ = contract
    result = invocation.validate(root, "invocation.json", **kwargs)
    prompt = kwargs["prompt"].read_text()
    assert result["manifest"] == value["manifest"]
    assert plan["round_id"] in prompt and value["manifest"]["sha256"] in prompt
    assert "round03-package" not in prompt and "reviewer-a" in prompt
    assert not Path(value["session"]["session_root"]).exists()
    invocation.reserve(root, "invocation.json")
    marker = Path(value["session"]["session_root"]) / "invocation.json"
    assert marker.is_file() and marker.stat().st_size > 0
    assert invocation.validate(root, "invocation.json", **kwargs, fresh=False) == result
    with pytest.raises(ValueError, match="session root already exists"):
        invocation.validate(root, "invocation.json", **kwargs)
    with pytest.raises(FileExistsError):
        invocation.reserve(root, "invocation.json")


@pytest.mark.parametrize("field,replacement,error", [
    ("manifest_path", "manifest.json", "Supplied package differs"),
    ("output", Path("/different/output"), "output root differs"),
    ("runtime", {"git_head": "b" * 40}, "runtime changed"),
])
def test_supplied_package_output_and_runtime_must_agree(contract, field, replacement, error):
    root, _, _, _, kwargs, _ = contract
    kwargs[field] = replacement
    with pytest.raises(ValueError, match=error):
        invocation.validate(root, "invocation.json", **kwargs)


@pytest.mark.parametrize("purpose", [None, "engineering_prerequisites"])
def test_engineering_and_legacy_packages_cannot_be_scientific_authorization(contract, purpose):
    root, _, manifest, _, kwargs, put = contract
    if purpose:
        manifest["package_purpose"] = purpose
    else:
        manifest.pop("package_purpose")
    put("future-manifest.json", manifest)
    with pytest.raises(ValueError, match="Engineering-only or undeclared"):
        invocation.validate(root, "invocation.json", **kwargs)


def mutate_plan(root, plan, manifest, put):
    put("instruction-plan.json", plan)
    for item in manifest["files"]:
        if item["path"] == "instruction-plan.json":
            item["sha256"] = invocation.pin(root, item["path"])["sha256"]
    put("future-manifest.json", manifest)


@pytest.mark.parametrize("field,value,error", [
    ("round_id", "previous-round", "manifest ID or path mismatch"),
    ("manifest_path", "old-round03/manifest.json", "manifest ID or path mismatch"),
    ("read_paths", ["private-originals/old-labels.json"], "Allowed navigation"),
    ("instruction_paths", ["authority.txt"], "Instruction paths differ"),
])
def test_package_pinned_instruction_mismatch_is_rejected(contract, field, value, error):
    root, plan, manifest, _, kwargs, put = contract
    plan[field] = value
    mutate_plan(root, plan, manifest, put)
    with pytest.raises(ValueError, match=error):
        invocation.validate(root, "invocation.json", **kwargs)


def test_matching_new_hash_cannot_make_stale_freeform_prompt_valid(contract):
    root, _, _, value, kwargs, put = contract
    kwargs["prompt"].write_text("Use old round03-package/manifest.json and completed reviewer roots.")
    value["prompt"] = invocation.pin(root, "generated.prompt.md")
    put("invocation.json", value)
    with pytest.raises(ValueError, match="differs from verified structured instructions"):
        invocation.validate(root, "invocation.json", **kwargs)


def test_completed_session_cannot_be_reused_with_a_fresh_child_output(contract):
    root, plan, manifest, value, kwargs, put = contract
    session = Path(value["session"]["session_root"])
    (session / "previous-output").mkdir(parents=True)
    (session / "previous-output/FINAL_REPORT.md").write_text("Completed retained result")
    assert not kwargs["output"].exists()
    with pytest.raises(ValueError, match="session root already exists"):
        invocation.validate(root, "invocation.json", **kwargs)
    assert (session / "previous-output/FINAL_REPORT.md").read_text() == "Completed retained result"


def test_modified_production_receipt_and_session_reservation_fail_closed(contract):
    root, _, _, _, kwargs, put = contract
    invocation.reserve(root, "invocation.json")
    put("production/receipt.json", {"other": "receipt"})
    with pytest.raises(ValueError, match="production receipt changed"):
        invocation.validate(root, "invocation.json", **kwargs, fresh=False)


def test_session_clone_and_overlapping_work_are_not_interchangeable(contract):
    root, plan, manifest, _, kwargs, put = contract
    other = copy.deepcopy(plan["sessions"][0])
    other["reviewer_id"] = "reviewer-b"
    other["session_root"] = str(root / ".temp/other")
    other["output_root"] = str(root / ".temp/other/worker")
    plan["sessions"].append(other)
    mutate_plan(root, plan, manifest, put)
    with pytest.raises(ValueError, match="distinct reviewer clones"):
        invocation.validate(root, "invocation.json", **kwargs)


def test_209_adjudication_rejected_without_a_typed_initial_seals_and_results_contract(contract):
    root, plan, manifest, value, kwargs, put = contract
    plan["phase"] = "evidence_adjudication"
    mutate_plan(root, plan, manifest, put)
    with pytest.raises(ValueError, match="Unsupported scientific phase"):
        invocation.validate(root, "invocation.json", **kwargs)
    with pytest.raises(ValueError, match="Unsupported scientific phase"):
        invocation.generated_prompt(plan, manifest, value["session"], {
            key: value[key] for key in ("manifest", "instructions")},
            invocation.instruction_templates(root, plan))


@pytest.mark.parametrize("legacy", [True, False])
def test_old_embedded_instruction_paths_cannot_reenter_via_pinned_assets(contract, legacy):
    root, plan, manifest, _, kwargs, put = contract
    path = root / "instructions.md"
    if legacy:
        path.write_bytes((ROOT / "scripts/adhoc/m5_review_20261116/round03-blinded-review.md")
                         .read_bytes())
    else:
        put("instructions.md", {"schema": invocation.TEMPLATE_SCHEMA,
                                "text": "Read .temp/round03-package/manifest.json."})
    for item in manifest["files"]:
        if item["path"] == "instructions.md":
            item["sha256"] = invocation.pin(root, item["path"])["sha256"]
    put("future-manifest.json", manifest)
    with pytest.raises(ValueError, match="structured templates|bound placeholders"):
        invocation.validate(root, "invocation.json", **kwargs)
