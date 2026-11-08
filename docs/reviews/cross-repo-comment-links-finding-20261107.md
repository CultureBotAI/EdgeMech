# Qualify cross-repository references in implementation evidence comments

The final read-only EdgeMech bundle review found incorrect destination context
in the prepared comments for CultureBotAI/culturebotai-claw issues 951 and 952.
The retained bodies are `docs/reviews/claw-951-implementation-evidence-20261107.md`
and `docs/reviews/claw-952-implementation-evidence-20261107.md`.

The first uses `EdgeMech #14 and #15` and `PR #2`. The second uses bare references
such as `MIM #1147`, `Trait #2082`, `Habitat #2313`, `Taxon #229`, and follow-ups
1144, 2083, 2311 and 226. When posted in CLAW, the numeric issue references link
to CLAW instead of the intended repositories. The explicit EdgeMech PR links
already present are correct.

Before posting, qualify every foreign reference with `CultureBotAI/<repo>#N`
or a direct GitHub link, including later repetitions of EdgeMech PR 2. Local
CLAW references can remain local. Retain the corrected comment bodies with the
final EdgeMech PR evidence. No source, runtime, tests or census rerun is needed.

This finding was recorded after the read-only pass. The reviewer did not edit
the prepared comments. The remaining completion claims, scientific scope,
source/output proof, final package hashes and unchanged census runtime passed
the review; final exact-head CI remains a separate post-push check.
