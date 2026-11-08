# Real native packet transport check

The retained `scripts/adhoc/run_native_packet_canary_20261107.py` transported the
three-row pinned MIM canary through `edgemech.packets.inherited_bundle`, then
reloaded and validated the saved canonical bundle and exact membership.

All three complete native envelopes survived unchanged: one inherited supported
mapping and two scoped withheld mappings. The canonical packet contains three
observations and three deferred/withheld decisions, with no claims, reviews or
new scientific approvals. This addresses EdgeMech #9.

The fixture explicitly uses `native_export_transport_fixture` occurrence IDs
and declares `kg_release_occurrences: false`. It tests transport preservation;
it does not fabricate matches to KG rows or contribute to the overlap census.

Verified artifacts under `workspace/validation-20261107/native-packet-conformance/`:

- Native input manifest: `2f0a74b3985f7e57a0a404897b2451529c66c444cfd12cdf025d9d419aaea730`.
- Native JSONL: `cb03a199754812e9a4a895013e3af981f5b0606966baf81936eafc3fbd2129c2` (25,392 bytes).
- Canonical bundle: `6d8c0d43c76c8101084a0385570e4780f0ae7c011ac29c921dc8c412c468c4a0`.
- Receipt: `11ae2bf579ac8a8c64397d65901836f90b0c0f4b118ddcaddb51fdba39b4a034`.

The run verified all 16 shared contract files against immutable CLAW commit
`1b5391d083ba85ac94e5279c3cba25ac4fde243c`. Independent read-only review checked
the helper, receipt, saved bundle, counts and explicit fixture scope.
