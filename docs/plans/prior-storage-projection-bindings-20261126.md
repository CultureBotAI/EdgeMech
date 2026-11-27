# Prior storage-projection bindings — issues #224 and #228

Direct report data, 2026-11-26. Independent baseline disposition remains pending.
This bounded readback reuses the retained wave replay, native structural audit
and source artifacts. It does not repeat a historical canary, storage mutation,
provider request, source restoration or full census verification.

The wave 3 worker-01 family has four review variants: an original canary, an
original eleven-case shard review, a canary storage projection and a twelve-case
storage projection. The original bundle retains twelve withheld decisions,
zero claims and two concern assessments per original occurrence, covering scope
and provenance. The canary's embedded review, decision and occurrence are reused
unchanged in the shard bundle. All twelve originals already belong to the
retained 593-ID decision index.

The projection reviews contain supported representation judgments with explicit
storage-only scope. They bind separate occurrence IDs and preserve the original
withheld meaning; they assert no independent scientific approval. These are
concrete occurrence-specific judgments, so the scientific_review=false flag is
not grounds to discard them. Their target identity domain must be retained for
the pending baseline decision.

The first twelve original/projection mappings match the pinned shard,
preflight envelopes and actual export rows. This readback then checked the same
mapping across all ten retained wave 3 shards:

| Check | Observed result |
| --- | --- |
| Shard files whose current hashes occur in the retained wave 3 review input pins | 10 of 10 |
| Declared case mappings | 120 |
| Distinct original IDs / distinct projection IDs | 120 / 120 |
| Intersection of the two ID sets | 0 |
| Distinct projection row numbers | 120 |
| Projection envelopes, including exact source-row strings, equal actual export rows | All 120 |
| Original and projection declared raw-row hashes agree | All 120 |
| Original ID set equals the retained authoritative wave decision set | Yes |
| Projection ID set equals the entire retained 120-row export | Yes |
| Union of assessed IDs in the 22 wave 3 native variants equals both domains | Yes |
| IDs outside the retained candidate union | 0 |

The actual export JSONL matches its manifest hash. Concatenating the manifest's
literal header row and the 120 exported source-row strings in their retained
order reproduces the declared source-member hash. This establishes retained
byte consistency for this small export. Occurrence IDs were not recomputed in
this unit, and original full-source rows were not reread. Matching the original
rows to the full census remains a separate gated task. No subject/predicate/object
join, inherited cohort coverage or merged identity is used.

The original cases declare source manifest
f585e55a616d3771f382c91c78713cb8d74812c7ba177576090ccd5f9e6654b2 and member
e6a846112ff8c769a8daa8a3c509c3390bd7b5e341c7998ce9188ebece9d4c9a.
The storage export instead declares source manifest
0b81139a9f50c9747328d1c97270b93183d0a7535e35a0a3459644688fb35cae and member
74c84f325b2264dbf45d677bdc5b6dbcc5464b2081476c1446ccfd32e700069a.
Equal row bytes across these domains do not make their occurrence IDs interchangeable.

| Retained artifact | SHA256 |
| --- | --- |
| Original canary review | 868d9fca66f4deabc7a070fc794dd0dd61d65d5e0e1f1e042ba21ea0762e6fc6 |
| Original worker-01 shard review | 14b18f27181bc1f9d2620b64e50e3a2e055ad434ce22e4e2aa1adda47e315a8a |
| Canary projection review | 1afc93594ab9a2363ba66faf4c78d387eacaacb63855ae8a3651886371583940 |
| Worker-01 shard projection review | 529d06657bf78a6a2efa078530ec4fb3a6ba36e2a2221278d5cd78784bf3cb14 |
| Original canary bundle | 36d3a80b106deeddbfe84d78f0e8f09c86b8347e93837b8a2982ce0be82b3e02 |
| Original worker-01 shard bundle | c563074ae2394dd9b924ce3dcd040c0d41b0fe1e40c8d353fecce421f4b686a9 |
| Worker-01 preflight | 02a4a986548255204e8e52a60dbeba4ff825f57f5ee6eb81aedf95d861abe8dd |
| Export manifest | 1d586dc8b407c2250761021b20d9ce2ff1e476f8fd998d86fad653ae9013514a |
| Export rows JSONL | 5f144708b361905510a549c6738ecb2a6c3c17dcd310a05c2968d74a916539bd |
| Authoritative wave bundle reused from earlier replay | e5f96cc5a742c3b5daf60f805ed8cc1f52d293d45aa1ba788aaa693a250626c5 |

| Shard | SHA256 |
| --- | --- |
| 01 | 43ed7ff3b132457a29152e2e97b9ccc04457fb2f873d261a6e06caa252ce8673 |
| 02 | a2e2a5e62198ed1669f417f6d0fbccfed73c78628e29d7316ee6ad148148c599 |
| 03 | a7ffead5e88049bce5ce521800068230526c73aa59e2be212c8c5577bac064c4 |
| 04 | 15f32999a7cfb4df07ccb28ff6176beed97541909729156eec9434709ea0a519 |
| 05 | 0e73fa9aaa523768961701885b24b4f94cab0bd850a5a6806c36e33cf1cac7da |
| 06 | 618df9b59a5ca0efe0bbab8cc52a4595a2281d1d4724bf63f14705da218cb2e3 |
| 07 | 68ae124e5c8c9db597c352755ffb361fc8210aa12dda9adbdce9cdb69eb4513b |
| 08 | e562bcea2a898dcf877e61ceb8228383a0b0b389befaaed43c7b1bb927e7b6ae |
| 09 | c22d085970927d2c4b04c6b3da30b009f41e8822f962c7aa1c1f311b1174c3ea |
| 10 | 7ee806386832fd1865de9f2fe3a8efb8384fae27f285d1bfc54a2b3f719f62a5 |

This readback adds no candidate IDs and assigns or excludes no baseline member.
It inspects the worker-01 review scope and the ten-shard mapping, not all 22
review bodies or every input of every review. The other waves require their own
retained mapping checks. A/B counts and cutoff remain unfrozen, scientific
coverage remains zero, and all existing census, archive-lineage, scientific
readiness and publication gates remain.
