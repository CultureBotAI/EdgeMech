"""Versioned physical columns; biological identities remain owned by pinned CLAW."""

import pyarrow as pa

AUTHORITATIVE = ("occurrences", "current_decisions", "bundles", "metadata", "coverage_counts")
DIMENSIONS = ("lifecycle", "review_state", "conflict_state", "disposition")


def _schema(fields):
    return pa.schema([
        pa.field(name, pa.int64() if kind == "int" else pa.string(), nullable=nullable)
        for name, kind, nullable in fields
    ])


TABLE_SCHEMAS = {
    "occurrences": _schema([
        ("occurrence_id", "str", False), ("member", "str", False),
        ("row_number", "int", False), ("row_sha256", "str", False),
        ("source_row", "str", False),
    ]),
    "current_decisions": _schema([
        ("occurrence_id", "str", False),
        *((name, "str", False) for name in DIMENSIONS), ("bundle_sha256", "str", True),
    ]),
    "bundles": _schema([
        ("bundle_sha256", "str", False), ("parent_revision", "str", False),
        ("revision", "str", False), ("document", "str", False),
    ]),
    "metadata": _schema([("key", "str", False), ("value", "str", False)]),
    "coverage_counts": _schema([
        ("dimension", "str", False), ("value", "str", False), ("count", "int", False),
    ]),
    **{name: _schema([
        ("bundle_sha256", "str", False), (identifier, "str", False),
        ("document", "str", False),
    ]) for name, identifier in (
        ("observations", "observation_id"), ("claims", "claim_id"), ("reviews", "review_id")
    )},
    "evidence": _schema([
        ("bundle_sha256", "str", False), ("review_id", "str", False),
        ("position", "int", False), ("kind", "str", False), ("document", "str", False),
    ]),
    "memberships": _schema([
        ("occurrence_id", "str", False), ("bundle_sha256", "str", False),
        ("position", "int", False),
    ]),
    "history": _schema([
        ("bundle_sha256", "str", False), ("sequence", "int", False),
        ("parent_revision", "str", False), ("revision", "str", False),
    ]),
}
TABLE_KEYS = {
    "occurrences": ("occurrence_id",), "current_decisions": ("occurrence_id",),
    "bundles": ("bundle_sha256",), "metadata": ("key",),
    "coverage_counts": ("dimension", "value"),
    "observations": ("bundle_sha256", "observation_id"),
    "claims": ("bundle_sha256", "claim_id"), "reviews": ("bundle_sha256", "review_id"),
    "evidence": ("bundle_sha256", "review_id", "position"),
    "memberships": ("occurrence_id", "bundle_sha256"), "history": ("bundle_sha256",),
}
