"""Phase two replays unchanged authored originals rather than trusting summary labels (#209)."""
from __future__ import annotations

import copy
import importlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_calibration_round import round_inputs as round_inputs
from test_m5_scientific_invocation import ROOT, invocation
from test_round03_initial_seal import SEAL
from test_round03_initial_seal import authored_round as authored_round

seals = importlib.import_module("seal_m5_round03_initial_20261116")
worker = importlib.import_module("run_m5_review_worker_20261116")


@pytest.fixture
def adjudication(authored_round, monkeypatch):
    root, authored, original_put = authored_round
    rounds = SEAL.rounds
    monkeypatch.setattr(invocation, "rounds", rounds)
    monkeypatch.setattr(seals, "rounds", rounds)

    def put(path, value):
        target = root / path
        if target.is_file():
            target.chmod(0o600)
        original_put(path, value)

    subprocess.run(["git", "-C", str(root), "remote", "add", "origin",
                    "https://github.com/CultureBotAI/EdgeMech.git"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture",
                    "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty",
                    "-qm", "Synthetic adjudication fixture"], check=True)
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    config = rounds.read(root, "package-2.json")
    config["package_purpose"] = invocation.PURPOSE
    shutil.copyfile(ROOT / invocation.HELPER, root / invocation.HELPER)
    config["files"].append({"path": invocation.HELPER, "role": "proof_adapter"})
    launcher = "scripts/adhoc/run_m5_review_worker_20261116.py"
    shutil.copyfile(ROOT / launcher, root / launcher)
    config["files"].append({"path": launcher, "role": "proof_adapter"})
    bootstrap_helper = "scripts/adhoc/prepare_calibration_20261115.py"
    shutil.copyfile(ROOT / bootstrap_helper, root / bootstrap_helper)
    config["files"].append({"path": bootstrap_helper, "role": "proof_adapter"})
    fresh = next(c for c in config["cases"] if c["case_id"] == "fresh-47")
    packet = rounds.read(root, fresh["packet_path"])
    put(str(worker.FRESH47 / "packet.json"), packet)
    put(str(worker.FRESH47 / "receipt.json"), {"occurrence_id": packet["occurrence_id"],
                                              "case_id": "fresh-47"})
    config["files"].extend({"path": str(worker.FRESH47 / name), "role": "bootstrap_input"}
                            for name in ("packet.json", "receipt.json"))
    put("instructions.md", {"schema": invocation.TEMPLATE_SCHEMA,
                            "text": "Use {{manifest_path}} and {{output_root}}."})
    for item in config["files"]:
        if item["role"] in {"instructions", "authority", "evidence", "view"}:
            item["visibility"] = "reviewer"
    initial_path = ".temp/original-package/manifest.json"
    initial_plan_path = ".temp/original-package/plan.json"
    sessions = []
    for rid in ("reviewer-a", "reviewer-b"):
        clone = root.parent / (root.name + "-" + rid)
        session_root = clone / ".temp" / rid
        sessions.append({"reviewer_id": rid, "workdir": str(clone),
                         "session_root": str(session_root),
                         "output_root": str(session_root / "worker")})
    original_plan = {"schema": invocation.PLAN_SCHEMA, "purpose": invocation.PURPOSE,
                     "round_id": config["round_id"], "manifest_path": initial_path,
                     "phase": "blinded_initial_review", "sessions": sessions,
                     "instruction_paths": ["instructions.md"],
                     "read_paths": [rounds.PROTOCOL, *[p["path"] for p in config["files"]
                                                     if p.get("visibility") == "reviewer"]]}
    put(initial_plan_path, original_plan)
    config["files"].append({"path": initial_plan_path, "role": "scientific_instructions"})
    put(".temp/original-package/config.json", config)
    rounds.freeze(root, ".temp/original-package/config.json", initial_path)
    original_plan, initial, bindings = invocation.checked_plan(root, initial_path, initial_plan_path)
    entries, extra_files = [], {}

    def add(path, role, visible=False):
        extra_files[path] = {"path": path, "role": role}
        if visible:
            extra_files[path]["visibility"] = "reviewer"
        return invocation.pin(root, path)

    add(initial_path, "initial_manifest")

    def make_readiness(session):
        from edgemech.occurrence_review import CATEGORIES, save_occurrence_review

        rid, clone = session["reviewer_id"], Path(session["workdir"])
        runtime = {"git_head": commit, "helper_sha256": invocation.pin(root, launcher)["sha256"],
                   "codex_path": "/fixture/native/codex", "codex_sha256": "c" * 64,
                   "host": "fixture-host", "python_prefix": str(clone / ".venv"),
                   "python_executable": str(clone / ".venv/bin/python3"),
                   "python_version": "3.13 synthetic recorded runtime", "python_sha256": "d" * 64,
                   "lock_sha256": invocation.pin(root, "uv.lock")["sha256"],
                   "distributions_sha256": "e" * 64, "environment_sha256": "f" * 64,
                   "repository_identity": worker.REPOSITORY,
                   "repository_origin": "https://github.com/CultureBotAI/EdgeMech.git"}
        entry = next(c for c in authored["cases"] if c["case_id"] == "fresh-47")
        draft = rounds.read(root, entry["review"])
        draft["source"]["git_revision"] = commit
        draft["review_id"] += "-readiness-" + rid
        draft["scientific_review"], draft["verdict"] = False, "not_assessed"
        for assessment in draft["assessments"]:
            dims = {d["name"]: d for d in assessment["dimensions"]}
            if dims["axis"]["value"] == "source_fidelity":
                dims["category"]["value"] = "NOT_ASSESSABLE"
                assessment["outcome"] = CATEGORIES["source_fidelity"]["NOT_ASSESSABLE"]
        draft_path = f".temp/{rid}/readiness-draft.json"
        put(draft_path, draft)
        # The fixture uses the real canonical save/readback path; only native
        # execution/environment observations below are explicitly synthetic.
        saved_result = save_occurrence_review(root, draft, fresh["packet_path"], entry["proofs"])
        spec = worker.production_spec(root, draft_path, fresh["packet_path"], entry["proofs"], initial_path)
        spec["workdir"] = str(clone)
        outputs = worker.inspect_production_pair(root, spec)
        for value in [*spec["inputs"].values(), *spec["source_inputs"], *outputs.values()]:
            if value["path"] not in {p["path"] for p in config["files"]}:
                add(value["path"], "initial_readiness")
        output = Path(f".temp/{rid}/readiness")
        start = datetime.now(timezone.utc).isoformat()
        artifacts, originals = [], {}
        for name in ("packet.json", "receipt.json"):
            path = str(output / name)
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / worker.FRESH47 / name, root / path)
            value = add(path, "initial_readiness")
            artifacts.append({"path": str(clone / path), "sha256": value["sha256"]})
            originals[name] = value["sha256"]
        result = {"status": "passed", "checks": [{"name": name, "passed": True}
                                                   for name in sorted(worker.CHECKS)],
                  "artifacts": artifacts}
        result_path = str(output / "canary-result.json")
        put(result_path, result)
        result_pin = add(result_path, "initial_readiness")
        validators = []
        commands = {
            "runtime_contracts": [runtime["python_executable"], "-B", "-m", "edgemech", "check-contracts"],
            "fresh47_packet_replay": [runtime["python_executable"], "-B",
                                      str(clone / "scripts/adhoc/prepare_calibration_20261115.py"),
                                      "--check", "fresh-47"],
            "production-package": [runtime["python_executable"], "-B",
                                   str(clone / "scripts/adhoc/calibration_round_20261116.py"),
                                   "--root", str(clone), "verify", "--manifest", initial_path],
        }
        for action in ("save", "check"):
            commands["production-" + action] = [
                runtime["python_executable"], "-B", "-m", "edgemech.occurrence_review", action,
                "--root", str(clone), "--review", spec["review"] if action == "check" else draft_path,
                "--packet", fresh["packet_path"], "--proofs", entry["proofs"]]
        results = {"production-package": rounds.verify(root, initial_path),
                   "production-save": saved_result,
                   "production-check": {k: v for k, v in saved_result.items()
                                        if k not in {"review", "review_sha256"}}}
        for name in ("runtime_contracts", "fresh47_packet_replay", "production-package",
                     "production-save", "production-check"):
            validation = {"name": name, "exit_code": 0, "command": commands[name]}
            stdout = json.dumps(results.get(name, {"synthetic_retained_validator": True})).encode()
            for stream, raw in (("stdout", stdout), ("stderr", b"")):
                path = str(output / f"validator-{name}.{stream}")
                (root / path).write_bytes(raw)
                validation[stream + "_sha256"] = add(path, "initial_readiness")["sha256"]
            validators.append(validation)
        bootstrap = {"artifacts": originals, "validators": validators[:2]}
        production = {"spec": spec, "outputs": outputs, "validators": validators[2:]}
        prompt_path = f".temp/{rid}/readiness-prompt.md"
        (root / prompt_path).write_text("Synthetic operational readiness fixture\n")
        prompt = add(prompt_path, "initial_readiness")
        state = {"schema": worker.SCHEMA, **runtime, "ending_git_head": commit,
                 "status": "passed", "exit_code": 0, "role": "canary", "workdir": str(clone),
                 "output_root": str(clone / output), "started_at": start,
                 "finished_at": datetime.now(timezone.utc).isoformat(),
                 "independent_replay": bootstrap, "production": production, "production_plan": spec,
                 "prompt_path": str(clone / prompt_path), "prompt_sha256": prompt["sha256"],
                 "executed_prompt_sha256": "0" * 64}
        state_path = str(output / "metadata.json")
        put(state_path, state)
        state_pin = add(state_path, "initial_readiness")
        receipt = {"schema": worker.SCHEMA, **runtime, "status": "passed",
                   "scope": worker.PRODUCTION_SCOPE, "metadata_sha256": state_pin["sha256"],
                   "result_sha256": result_pin["sha256"], "result": result,
                   "independent_replay": bootstrap, "production": production,
                   "prompt_sha256": prompt["sha256"], "executed_prompt_sha256": "0" * 64}
        receipt_path = str(output / "canary-receipt.json")
        put(receipt_path, receipt)
        receipt_pin = add(receipt_path, "initial_readiness")
        replay = {"path": str(clone / receipt_path), "sha256": receipt_pin["sha256"],
                  "current_replay": bootstrap, "production_replay": production}
        return runtime, receipt_pin, replay

    for index, session in enumerate(sessions):
        rid = session["reviewer_id"]
        sid = "00000000-0000-4000-8000-00000000000" + str(index)
        identity = {**authored["reviewer"], "id": rid, "session_id": sid}
        runtime, readiness, canary_replay = make_readiness(session)
        start = datetime.now(timezone.utc).isoformat()
        authored_copy = {"reviewer": identity, "canonical_identity": rid, "cases": []}
        for case in authored["cases"]:
            proof_path = f".temp/{rid}/drafts/{case['case_id']}/proofs.json"
            review_path = f".temp/{rid}/drafts/{case['case_id']}/review.json"
            proof = rounds.read(root, case["proofs"])
            proof["reviewer"] = identity
            put(proof_path, proof)
            review = rounds.read(root, case["review"])
            review["reviewer"]["identity"] = rid
            review["source"]["git_revision"] = commit
            review["review_id"] += "-" + rid
            review["source"]["inputs"] = [p for p in review["source"]["inputs"]
                                          if p["path"] != case["proofs"]]
            review["source"]["inputs"].append({**invocation.pin(root, proof_path), "role": "proof"})
            put(review_path, review)
            add(review_path, "initial_authored_review", True)
            add(proof_path, "initial_proof_sidecar", True)
            authored_copy["cases"].append({"case_id": case["case_id"],
                                           "review": review_path, "proofs": proof_path})
        config_path = f".temp/{rid}/authored.json"
        put(config_path, authored_copy)
        add(config_path, "initial_config")
        sealed = seals.seal(root, initial_path, config_path, f".temp/{rid}/initial")
        matrix_pin = add(sealed["matrix"]["path"], "initial_matrix", True)
        receipt_pin = add(matrix_pin["path"] + ".receipt.json", "initial_receipt", True)
        seal_pin = add(sealed["seal"]["path"], "initial_seal", True)
        receipt = rounds.read(root, receipt_pin["path"])
        prompt_path = f".temp/{rid}/invocation.prompt.md"
        (root / prompt_path).write_bytes(invocation.generated_prompt(
            original_plan, initial, session, bindings,
            invocation.instruction_templates(root, original_plan)))
        prompt = add(prompt_path, "initial_prompt")
        original = {"schema": invocation.SCHEMA, "purpose": invocation.PURPOSE,
                    "round_id": initial["round_id"], **bindings,
                    "runtime": runtime, "production_receipt": readiness,
                    "session": session, "prompt": prompt}
        original_path = f".temp/{rid}/invocation.json"
        put(original_path, original)
        original_pin = add(original_path, "initial_invocation")
        output = Path(session["output_root"]).relative_to(session["workdir"])
        metadata_path, events_path = str(output / "metadata.json"), str(output / "events.jsonl")
        put(metadata_path, {"schema": worker.SCHEMA, **original["runtime"], "ending_git_head": commit,
                            "status": "completed", "exit_code": 0, "role": "reviewer",
                            "workdir": session["workdir"], "output_root": session["output_root"],
                            "prompt_sha256": prompt["sha256"], "started_at": start,
                            "finished_at": datetime.now(timezone.utc).isoformat(),
                            "canary": canary_replay, "ending_replay": canary_replay,
                            "scientific_invocation": {**original_pin, "manifest": bindings["manifest"],
                                "session": session, "scope": "invocation_coherence_not_scientific_approval"}})
        put(events_path, {"type": "thread.started", "thread_id": sid})
        events_pin = add(events_path, "initial_worker_events")
        native_path = f".temp/{rid}/native-session.jsonl"
        (root / native_path).write_text("\n".join(json.dumps(event) for event in [
            {"type": "session_meta", "payload": {"id": sid}},
            {"type": "turn_context", "payload": {"model": identity["model"]}}]) + "\n")
        native_pin = add(native_path, "initial_native_session")
        identity_path = f".temp/{rid}/identity.json"
        put(identity_path, {"schema": "edgemech-worker-identity/v1", "session_id": sid,
                            "model": identity["model"], "events": events_pin,
                            "native_session": {"path": "/private/native/session.jsonl",
                                               "sha256": native_pin["sha256"]}})
        entries.append({"position": ("reviewer_a", "reviewer_b")[index], "reviewer": identity,
                        "saved_at": receipt["saved_at"], "matrix": matrix_pin,
                        "receipt": receipt_pin, "seal": seal_pin, "invocation": original_pin,
                        "metadata": add(metadata_path, "initial_worker_metadata"),
                        "identity": add(identity_path, "initial_worker_identity"),
                        "events": events_pin, "native_session": native_pin})
    comparison_path = ".temp/comparison.json"
    put(comparison_path, rounds.compare(root, initial_path, *(e["matrix"]["path"] for e in entries)))
    comparison = add(comparison_path, "initial_comparison", True)
    phase_config = copy.deepcopy(config)
    for item in phase_config["files"]:
        if item["role"] == "instructions":
            item.pop("visibility", None)
    template_path = ".temp/adjudication/instructions.json"
    put(template_path, {"schema": invocation.TEMPLATE_SCHEMA,
                        "text": "Assess the sealed inputs of {{round_id}} under {{output_root}}."})
    phase_config["files"].extend(extra_files.values())
    phase_config["files"].append({"path": template_path, "role": "instructions", "visibility": "reviewer"})
    phase_path, plan_path = ".temp/adjudication/manifest.json", ".temp/adjudication/plan.json"
    adjudicator = {"reviewer_id": "adjudicator", "workdir": str(root),
                   "session_root": str(root / ".temp/new-adjudicator"),
                   "output_root": str(root / ".temp/new-adjudicator/worker")}
    plan = {"schema": invocation.ADJUDICATION_PLAN_SCHEMA, "purpose": invocation.PURPOSE,
            "round_id": config["round_id"], "manifest_path": phase_path,
            "phase": "evidence_adjudication", "sessions": [adjudicator],
            "instruction_paths": [template_path],
            "read_paths": [rounds.PROTOCOL, *[p["path"] for p in phase_config["files"]
                                            if p.get("visibility") == "reviewer"]],
            "adjudication": {"schema": invocation.ADJUDICATION_SCHEMA,
                             "initial_manifest": invocation.pin(root, initial_path),
                             "runtime_git_head": commit, "reviewers": entries,
                             "comparison": comparison}}
    put(plan_path, plan)
    phase_config["files"].append({"path": plan_path, "role": "scientific_instructions"})
    put(".temp/adjudication/config.json", phase_config)
    rounds.freeze(root, ".temp/adjudication/config.json", phase_path)
    manifest = rounds.read(root, phase_path)
    return root, plan, manifest, put


def repin(adjudication, *paths):
    root, plan, manifest, put = adjudication
    plan_path = ".temp/adjudication/plan.json"
    put(plan_path, plan)
    for item in manifest["files"]:
        if item["path"] in {plan_path, *paths}:
            item["sha256"] = invocation.pin(root, item["path"])["sha256"]
    put(plan["manifest_path"], manifest)


def check(adjudication):
    root, plan, _, _ = adjudication
    return invocation.checked_plan(root, plan["manifest_path"], ".temp/adjudication/plan.json")


def test_complete_phase_replays_real_authored_seals_and_keeps_originals(adjudication):
    root, plan, _, put = adjudication
    originals = {item[field]["path"]: invocation.pin(root, item[field]["path"])["sha256"]
                 for item in plan["adjudication"]["reviewers"] for field in ("matrix", "seal", "receipt")}
    checked, manifest, bindings = check(adjudication)
    session = checked["sessions"][0]
    prompt = invocation.generated_prompt(checked, manifest, session, bindings,
                                         invocation.instruction_templates(root, checked))
    assert b"separate evidence adjudicator" in prompt and b"reviewer_a" in prompt
    assert b"every resolved claim and model label, including agreements" in prompt
    assert b"native-session.jsonl" not in prompt and b"invocation.prompt.md" not in prompt
    assert b"Use seal_m5_round03_initial" not in prompt
    assert all(invocation.pin(root, path)["sha256"] == sha for path, sha in originals.items())
    put(".temp/adjudication/readiness.json", {"fixture": "not operational validation"})
    current_runtime = {"git_head": plan["adjudication"]["runtime_git_head"]}
    envelope = {
        "schema": invocation.SCHEMA, "purpose": invocation.PURPOSE, "round_id": plan["round_id"],
        **bindings, "session": session, "runtime": current_runtime,
        "production_receipt": invocation.pin(root, ".temp/adjudication/readiness.json"),
        "prompt": {"path": ".temp/adjudication/generated.md", "sha256": invocation.rounds.digest(prompt)}}
    put(".temp/adjudication/invocation.json", envelope)
    (root / ".temp/adjudication/generated.md").write_bytes(prompt)
    kwargs = {"manifest_path": plan["manifest_path"], "runtime": current_runtime,
              "receipt_path": root / ".temp/adjudication/readiness.json",
              "output": Path(session["output_root"]), "prompt": root / ".temp/adjudication/generated.md"}
    invocation.validate(root, ".temp/adjudication/invocation.json", **kwargs)
    # Even a coherent new envelope and actual launcher runtime cannot switch to
    # another (including docs-only) Git commit between initial and final phases.
    wrong = copy.deepcopy(envelope)
    wrong["runtime"] = {"git_head": "f" * 40}
    put(".temp/adjudication/invocation.json", wrong)
    with pytest.raises(ValueError, match="Adjudicator Git head differs"):
        invocation.validate(root, ".temp/adjudication/invocation.json",
                            **{**kwargs, "runtime": wrong["runtime"]})
    put(".temp/adjudication/invocation.json", envelope)
    invocation.reserve(root, ".temp/adjudication/invocation.json")
    invocation.validate(root, ".temp/adjudication/invocation.json", **kwargs, fresh=False)
    with pytest.raises(ValueError, match="already exists"):
        invocation.validate(root, ".temp/adjudication/invocation.json", **kwargs)


@pytest.mark.parametrize("damage,message", [
    ("missing_reviewer", "exactly two"), ("swapped_positions", "swapped initial reviewer"),
    ("swapped_matrix", "identity was swapped"), ("changed_saved_at", "timestamps changed"),
    ("runtime_commit", "another runtime commit"), ("wrong_initial_manifest", "not package-pinned"),
    ("hidden_matrix", "exposure mismatch"), ("omit_seal_dependency", "dependency is outside"),
    ("changed_comparison", "deterministic replay"), ("initial_clone_reused", "separate identity and clone"),
])
def test_incomplete_swapped_or_changed_phase_inputs_rejected(adjudication, damage, message):
    root, plan, manifest, put = adjudication
    binding = plan["adjudication"]
    a, b = binding["reviewers"]
    repin_paths = []
    if damage == "missing_reviewer":
        binding["reviewers"].pop()
    elif damage == "swapped_positions":
        binding["reviewers"].reverse()
    elif damage == "swapped_matrix":
        a["matrix"] = b["matrix"]
    elif damage == "changed_saved_at":
        a["saved_at"] = "2000-01-01T00:00:00Z"
    elif damage == "runtime_commit":
        binding["runtime_git_head"] = "d" * 40
    elif damage == "wrong_initial_manifest":
        binding["initial_manifest"]["path"] = ".temp/other-round/manifest.json"
    elif damage == "hidden_matrix":
        item = next(p for p in manifest["files"] if p["path"] == a["matrix"]["path"])
        item.pop("visibility")
        plan["read_paths"].remove(item["path"])
    elif damage == "omit_seal_dependency":
        manifest["files"] = [p for p in manifest["files"] if p["path"] != ".temp/reviewer-a/authored.json"]
    elif damage == "changed_comparison":
        path = binding["comparison"]["path"]
        comparison = invocation.rounds.read(root, path)
        comparison["reviewers"].reverse()
        put(path, comparison)
        binding["comparison"] = invocation.pin(root, path)
        repin_paths.append(path)
    elif damage == "initial_clone_reused":
        original = invocation.rounds.read(root, a["invocation"]["path"])
        clone = original["session"]["workdir"]
        plan["sessions"][0].update(workdir=clone, session_root=clone + "/.temp/new-adjudicator",
                                    output_root=clone + "/.temp/new-adjudicator/worker")
    repin(adjudication, *repin_paths)
    with pytest.raises(ValueError, match=message):
        check(adjudication)


@pytest.mark.parametrize("field,mutation,message", [
    ("metadata", {"schema": "not-the-launcher"}, "did not complete"),
    ("metadata", {"status": "running"}, "did not complete"),
    ("metadata", {"ending_git_head": "f" * 40}, "did not complete"),
    ("metadata", {"finished_at": "1999-01-01T00:00:00Z"}, "must precede"),
    ("identity", {"model": "different-model"}, "observed identity mismatch"),
])
def test_rehashed_wrong_session_provenance_is_not_accepted(adjudication, field, mutation, message):
    root, plan, _, put = adjudication
    entry = plan["adjudication"]["reviewers"][0]
    path = entry[field]["path"]
    doc = invocation.rounds.read(root, path)
    doc.update(mutation)
    put(path, doc)
    entry[field] = invocation.pin(root, path)
    repin(adjudication, path)
    with pytest.raises(ValueError, match=message):
        check(adjudication)


def test_missing_original_native_session_never_launches(adjudication):
    root, plan, _, _ = adjudication
    path = root / plan["adjudication"]["reviewers"][0]["native_session"]["path"]
    path.unlink()
    with pytest.raises(ValueError, match="Missing input"):
        check(adjudication)


def test_217_wrong_adjudicator_commit_cannot_publish_invocation_files(adjudication, monkeypatch):
    root, plan, _, put = adjudication
    native = root / ".temp/synthetic-native-binary"
    native.write_bytes(b"fixture executable identity")
    put(".temp/phase-readiness.json", {"codex_path": str(native)})
    monkeypatch.setattr(invocation, "subprocess", SimpleNamespace(check_output=lambda *a, **k: "f" * 40))
    monkeypatch.setattr(worker, "runtime_bindings", lambda *a: {})
    monkeypatch.setattr(worker, "repository_bindings", lambda *a: {})
    monkeypatch.setattr(worker, "verify_receipt", lambda *a, **kw: pytest.fail("commit mismatch must fail first"))
    output = ".temp/forbidden-invocation.json"
    with pytest.raises(ValueError, match="Adjudicator Git head differs"):
        invocation.prepare(root, plan["manifest_path"], ".temp/adjudication/plan.json",
                           "adjudicator", ".temp/phase-readiness.json", output)
    assert not (root / output).exists()
    assert not (root / (output + ".prompt.md")).exists()


def replace_original(adjudication, original):
    """Rehash a substituted envelope and matching metadata, exercising semantic linkage."""
    root, plan, _, put = adjudication
    entry = plan["adjudication"]["reviewers"][0]
    path = entry["invocation"]["path"]
    put(path, original)
    entry["invocation"] = invocation.pin(root, path)
    metadata = invocation.rounds.read(root, entry["metadata"]["path"])
    metadata["scientific_invocation"]["sha256"] = entry["invocation"]["sha256"]
    metadata.update(original["runtime"])
    put(entry["metadata"]["path"], metadata)
    entry["metadata"] = invocation.pin(root, entry["metadata"]["path"])
    repin(adjudication, path, entry["metadata"]["path"])


@pytest.mark.parametrize("damage,message", [
    ("missing_receipt", "readiness dependency is not package-pinned"),
    ("other_clone_receipt", "receipt does not match the complete initial runtime"),
    ("incomplete_runtime", "complete maintained launcher bindings"),
    ("wrong_helper", "launcher or lock hash differs"),
    ("wrong_lock", "launcher or lock hash differs"),
    ("wrong_python_clone", "original isolated EdgeMech clone"),
    ("unbound_canonical", "readiness dependency is not package-pinned"),
])
def test_217_rehashed_incomplete_or_substituted_readiness_is_rejected(adjudication, damage, message):
    root, plan, manifest, _ = adjudication
    a, b = plan["adjudication"]["reviewers"]
    original = invocation.rounds.read(root, a["invocation"]["path"])
    if damage == "missing_receipt":
        original["production_receipt"] = {"path": ".temp/nonexistent-readiness.json", "sha256": "c" * 64}
    elif damage == "other_clone_receipt":
        original["production_receipt"] = invocation.rounds.read(root, b["invocation"]["path"])["production_receipt"]
    elif damage == "incomplete_runtime":
        original["runtime"] = {key: original["runtime"][key] for key in ("git_head", "helper_sha256")}
    elif damage == "wrong_helper":
        original["runtime"]["helper_sha256"] = "1" * 64
    elif damage == "wrong_lock":
        original["runtime"]["lock_sha256"] = "1" * 64
    elif damage == "wrong_python_clone":
        original["runtime"]["python_prefix"] = "/another-clone/.venv"
    elif damage == "unbound_canonical":
        receipt = invocation.rounds.read(root, original["production_receipt"]["path"])
        path = receipt["production"]["outputs"]["markdown"]["path"]
        manifest["files"] = [item for item in manifest["files"] if item["path"] != path]
    replace_original(adjudication, original)
    with pytest.raises(ValueError, match=message):
        check(adjudication)


@pytest.mark.parametrize("damage,message", [
    ("wrong_clone", "metadata is incomplete or belongs to another clone"),
    ("fake_command", "differs from maintained command"),
    ("fake_output", "validator output differs from retained replay"),
])
def test_217_rehashed_canary_lineage_must_replay_the_real_path(adjudication, damage, message):
    root, plan, _, put = adjudication
    entry = plan["adjudication"]["reviewers"][0]
    original = invocation.rounds.read(root, entry["invocation"]["path"])
    receipt_path = original["production_receipt"]["path"]
    metadata_path = str(Path(receipt_path).parent / "metadata.json")
    receipt = invocation.rounds.read(root, receipt_path)
    state = invocation.rounds.read(root, metadata_path)
    paths = [receipt_path, metadata_path]
    if damage == "wrong_clone":
        state["workdir"] = "/another-clone"
    else:
        validation = receipt["production"]["validators"][1]
        if damage == "fake_command":
            validation["command"] = [original["runtime"]["python_executable"], "fake-save"]
        else:
            path = str(Path(receipt_path).parent / "validator-production-save.stdout")
            put(path, {"claimed_success": True})
            validation["stdout_sha256"] = invocation.pin(root, path)["sha256"]
            paths.append(path)
        state["production"] = receipt["production"]
    put(metadata_path, state)
    receipt["metadata_sha256"] = invocation.pin(root, metadata_path)["sha256"]
    put(receipt_path, receipt)
    original["production_receipt"] = invocation.pin(root, receipt_path)
    replace_original(adjudication, original)
    repin(adjudication, *paths)
    with pytest.raises(ValueError, match=message):
        check(adjudication)
