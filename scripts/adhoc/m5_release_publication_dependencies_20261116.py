#!/usr/bin/env python3
"""Read the exact canonical full-release dependency gap without running producers.

2026-11-16 provenance: parse only merge.yaml, the lazy registry/constants and
its selected producer class definitions. Inspect explicitly configured graph
paths and whole-source completion records directly, including ignored files.
Read release-preflight policy pins without hashing or downloading bulk inputs.
Presence is not freshness or completion validation. A future successful
ontologies/BacDive/BactoTraits chain still covers only part of canonical merge.
"""

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


def identity(path):
    """Bind small implementation/configuration files read for this audit."""
    payload = path.read_bytes()
    return {"path": str(path), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def inspect(root):
    """Derive source requirements from maintained code rather than a remembered source list."""
    pins = {}

    def parse(relative):
        path = root / relative
        pins[relative] = identity(path)
        return ast.parse(path.read_text())

    constants = {}
    for node in parse("kg_microbe/transform_utils/constants.py").body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    registry = {}
    for node in parse("kg_microbe/transform.py").body:
        if isinstance(node, ast.Assign) and any(isinstance(key, ast.Name) and key.id == "DATA_SOURCES" for key in node.targets):
            for key, value in zip(node.value.keys, node.value.values):
                name = constants[key.id] if isinstance(key, ast.Name) else ast.literal_eval(key)
                registry[name] = ast.literal_eval(value.args[0])
    dependencies = {}

    def declaration(source):
        if source in dependencies:
            return dependencies[source]
        module_name, class_name = registry[source].rsplit(".", 1)
        relative = module_name.replace(".", "/") + ".py"
        module = parse(relative)
        cls = next(node for node in module.body if isinstance(node, ast.ClassDef) and node.name == class_name)
        declarations = [node for node in cls.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "TRANSFORM_INPUTS" for target in node.targets)]

        def evaluate(expression):
            if isinstance(expression, ast.Name):
                return constants[expression.id]
            if isinstance(expression, ast.Attribute) and expression.attr == "TRANSFORM_INPUTS":
                inherited = next(key for key, value in registry.items() if value.endswith("." + expression.value.id))
                return declaration(inherited)["upstreams"]
            if isinstance(expression, (ast.Tuple, ast.List)):
                result = []
                for value in expression.elts:
                    result.extend(evaluate(value.value) if isinstance(value, ast.Starred) else [evaluate(value)])
                return result
            return ast.literal_eval(expression)

        if declarations:
            node = declarations[0]
            result = {"implementation": relative, "line": node.lineno, "upstreams": evaluate(node.value)}
        else:
            parse("kg_microbe/transform_utils/transform.py")
            result = {"implementation": relative, "line": cls.lineno, "upstreams": [],
                      "inherited_empty_default": "kg_microbe/transform_utils/transform.py:Transform.TRANSFORM_INPUTS"}
        dependencies[source] = result
        return result

    config_path = root / "merge.yaml"
    pins["merge.yaml"] = identity(config_path)
    config = yaml.safe_load(config_path.read_text())
    sources, producers = {}, {}
    for name, source in config["merged_graph"]["source"].items():
        files = source["input"]["filename"]
        directories = {str(Path(value).parent) for value in files}
        if len(directories) != 1:
            raise ValueError(f"Source spans unexpected producer directories: {name}")
        relative = directories.pop()
        directory_name = Path(relative).name
        producer = "prego" if directory_name == "prego_habitat" else directory_name
        declaration(producer)
        sources[name] = {"producer": producer, "directory": relative,
                         "configured_inputs": [{"path": value, "present": (root / value).is_file()} for value in files]}
        if producer not in producers:
            records = {}
            for filename in ("source_finalization.json", "source_fingerprint.json"):
                path = root / relative / filename
                records[filename] = {"present": path.is_file()}
                if path.is_file():
                    records[filename].update(identity(path))
                    data = json.loads(path.read_text())
                    records[filename]["record_version"] = data.get("version")
                    records[filename]["record_source"] = data.get("source")
            producers[producer] = {"directory": relative, "canonical_source_keys": [],
                                   "dependency_declaration": dependencies[producer], "completion_records": records,
                                   "freshness_verified": False}
        producers[producer]["canonical_source_keys"].append(name)
    # This module exposes small read-only pin collectors; do not run bulk preflight.
    sys.path.insert(0, str(root))
    from kg_microbe.utils import release_preflight

    for name, _ in (*release_preflight.PINNING_POLICIES, *release_preflight.DERIVED_PINS):
        pins[name] = identity(root / name)
    for name in ("kg_microbe/utils/release_preflight.py", "kg_microbe/merge_utils/source_freshness.py",
                 "kg_microbe/merge_utils/merge_kg.py", ".github/workflows/release.yml"):
        pins[name] = identity(root / name)
    planned = {"ontologies", "bacdive", "bactotraits"}
    return {"profile": "m5-full-release-dependency-gap/v1", "observed_at": datetime.now(timezone.utc).isoformat(),
            "kg_root": str(root), "producer_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
            "helper": identity(Path(__file__).resolve()), "implementation_config_policy_pins": pins,
            "canonical_source_key_count": len(sources), "canonical_producer_count": len(producers),
            "canonical_sources": sources, "producers": producers,
            "planned_chain": sorted(planned),
            "remaining_producers_after_successful_planned_chain": sorted(set(producers) - planned),
            "remaining_source_keys_after_successful_planned_chain": [key for key, value in sources.items() if value["producer"] not in planned],
            "reviewed_release_raw_pins": release_preflight.reviewed_release_pins(root),
            "derived_raw_pins": release_preflight.reviewed_release_pins(root, policies=release_preflight.DERIVED_PINS),
            "additional_preflight_requirement": "NCIT SQLite authority validation; NCIT is used by whole ontologies, ontologies_stubs and MediaDive. Existing UPA JSON must match its derived pin.",
            "scope": "Exact configured paths were checked directly, including ignored files. Presence only; no current freshness, graph acceptance or publication validation. No graph scans, producer execution or downloads."}


def main():
    """Keep each audit in a fresh exclusive output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kg-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = inspect(args.kg_root.resolve(strict=True))
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "dependency-gap.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "canonical_source_keys": result["canonical_source_key_count"],
                      "producers": result["canonical_producer_count"],
                      "remaining_after_planned_chain": result["remaining_producers_after_successful_planned_chain"]}, indent=2))


if __name__ == "__main__":
    main()
