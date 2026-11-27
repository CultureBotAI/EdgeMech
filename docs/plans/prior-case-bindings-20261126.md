# Prior case-index binding observations — issues #224 and #228

Directly authored on 2026-11-26 from bounded read-only artifact inspection.
Independent baseline qualification remains pending. No historical job, census
verification, provider retrieval or canonical save was repeated.

The retained additional-metadata inventory contains 166 case-row instances
without a literal occurrence ID. These are not 166 new occurrence candidates:

| Retained shape | Row instances | Observed binding |
| --- | ---: | --- |
| Twelve synthetic reviewer matrices | 120 | Six identical copies for each of two fixture identities; no assessment fields or occurrence IDs |
| Wave 3 shard 01 case assessments | 11 | Case indices 2–12 bind to 11 exact shard occurrence IDs |
| Wave 4 shard 01 case assessments | 35 | Case indices 2–36 bind to 35 exact anchor occurrence IDs |

All twelve matrices have exactly the declared synthetic case sequence `case-0`
through `case-9`, `original-package`, the fixture model/identity markers and no
other case fields. This matches the construction in
`test_round03_reviewer_binding_uses_each_original_clone` in
`tests/test_m5_round03_publication_compatibility.py`. This is content evidence,
not an exclusion inferred from a directory name. The retained test source is
context for the construction; historical execution of that particular source
version has not been newly established.

For each wave, case indices and selected shard IDs are unique. The exact case
and shard byte hashes are both pinned by one embedded canonical review. Every
selected ID is a `snapshot_row` target of that review, appears in its assessment
targets, has a withheld case decision referencing that review, and already
appears in the retained 593-ID decision index. These 46 bindings add no IDs to
that retained candidate subset. This observation reuses the earlier maintained
wave replay; it does not replace source-row identity or full-census validation.

Wave 4 distinguishes its 35 newly assessed anchors from one unchanged canary
anchor reused in the 36-target document. First/median/last sample projections
and the declared cohort population supply context only. They do not create
additional individually assessed targets or population-wide scientific credit.
All selected shard records declare the same retained source manifest and member
pins. Exact membership in the campaign census remains a separate pending unit.

| Artifact role | SHA256 |
| --- | --- |
| Retained case-binding inventory | 6b6c63b287295d6ed41f2cd832f95d4ae2aaaec0b25bc1b316e9a6e20efc63ff |
| Fixture matrix variant A | afbe373fb1dc8d914bcc6f4a47813f5b00b9ef32dcff18d6a9df6465770b937d |
| Fixture matrix variant B | 0878bc72502f98510022621af4ef89958d486253da2a35863ddfabe0c979b60b |
| Inspected fixture-construction source | 4f254c1a33932fd5faa6cb116882be4472cf2f97d6b67e6f5edbf086378b0d4c |
| Wave 3 case assessments | e6ab434a995c70148b1aa024a06fb2f2dfbdfc07b08d6b5be258b64c51382195 |
| Wave 3 shard | 43ed7ff3b132457a29152e2e97b9ccc04457fb2f873d261a6e06caa252ce8673 |
| Wave 3 shard bundle | c563074ae2394dd9b924ce3dcd040c0d41b0fe1e40c8d353fecce421f4b686a9 |
| Wave 3 case decisions | 4f462a814340da4953e9523c3d969d9dcf8a1e5cdbc8fd9b458ae820ced374e2 |
| Wave 4 case assessments | 5b06a3d7f5fe24b001cf3d489d3e16d9d4916168a28bd7133a17473324d8c0ff |
| Wave 4 shard | eecf6c7bf434b22810a4863d60c3f96103b29b0c4368fdc53816f3757946a0d4 |
| Wave 4 shard bundle | b407984973f0dc6af15099d558e25e0c0d9599050c734fb215130cdd3da938fa |
| Wave 4 case decisions | ac05f48da27e44bb3bfda94be9385ed79368772d2df1847cc112594e652af2aa |
| Retained 593-ID index | 8e86be07e7de1e7e33339d4a50e4359ccb5d945af4b7e50ca63ab1ff1290f08e |
| Previously retained maintained wave replay | 4150f2f875cc76b2173274369b772cda3dccfd35facf106808b7bf0c5f9ba9de |

The private locator inventory and unchanged inputs remain available for
independent readback. This report is a proposed disposition of one bounded
metadata subset, not an exhaustive prior-assessment ledger. It does not qualify
other fixtures or the automated archive. A/B counts and cutoff remain unfrozen;
scientific coverage remains zero. All existing readiness gates remain.
