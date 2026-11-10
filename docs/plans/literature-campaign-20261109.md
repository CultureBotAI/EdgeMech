# Literature retrieval, quote verification and scientific adjudication

Follow-up to PR #33, merged on 2026-11-10; PR #38 now targets main.
The first production cohort is all 463 `infores:microbedecoder-literature`
occurrences from the pinned 17,637,435-occurrence census. There is no automatic
propagation of scientific judgments to other rows or shared-citation neighbors.

## Implemented workflow

1. `evidence_campaign.prepare_cohort` verifies pinned preparation shards and the
   census, recovers exact binary rows and canonical occurrence IDs, preserves all
   context columns, and deduplicates explicit DOI/PMID references. A source
   bibliography without an explicit identifier is retained, not guessed.
2. `literature_cache` serializes anonymous Europe PMC requests through a shared
   cache directory. Its nonblocking process lock prevents concurrent writers;
   persisted request timing applies across invocations. It uses a one-second
   minimum interval, three attempts, exponential backoff/jitter, Retry-After,
   bounded response sizes/timeouts, expiring cache entries and a 2 GiB disk
   reserve. Long server cooldowns stop work instead of sleeping indefinitely.
3. Metadata requires exact identifier equality and an unambiguous untruncated
   result. Abstracts and available open-access full text remain distinct. Full-text
   XML must contain the expected PMC identity. Source responses are stored by
   SHA-256; source text is a versioned derivative, never silently normalized into
   a quotation. This is a DOI/PMID cache, not a claim-equivalence cache.
4. `literature_adjudication` consumes explicit per-occurrence agent/human notes.
   It independently reconstructs text from retained response bytes, verifies
   contiguous quotes and offsets, checks the citation belongs to that occurrence,
   and emits the existing pinned CLAW RecordReview and curation-bundle contracts.
   Taxon, predicate, object, conditions/context and evidence scope must each have
   an explicit explanation. Quote matching alone never creates an assessment.
5. Unannotated rows remain `deferred/withheld`. Assessed source interpretations
   can be supported, concerning, unknown or not applicable. Even a supported
   source interpretation stays withheld from KG admission until a native scoped
   observation/claim is established. No synthetic assay identity is introduced.

All launchers are in `scripts/adhoc/`. Bulk cohort, cache, retrieval and canonical
review artifacts stay under ignored `workspace/`; explicit bounded reviewer
judgments live in `conf/literature_assessments/` for PR inspection.

## Citation encoding correction

The first strict UTF-8 check flagged 27 occurrences. KG-Microbe documents that
`source_citation_base64` preserves exact source-cell bytes, including rare
malformed UTF-8, while `source_citation` uses UTF-8 replacement decoding followed
by literal backslash/control-character escaping. The adapter now verifies that
exact source-specific display policy without altering the original bytes. A
remaining discrepancy is blocked. It does not apply this rule to unrelated
producers. The policy is documented in KG-Microbe's
`docs/MICROBEDECODER_SOURCE_CONTEXT.md` and implemented by
`MicrobeDecoderTransform._escape_literal` in `microbedecoder.py`.

The cohort has 33 explicit DOIs linked to 185 occurrences, plus 278 occurrences
with bibliography text but no explicit identifier. Those 278 need a separate
bibliographic-resolution workflow with title/author/year confirmation.

## Research basis and limits

[Europe PMC's API documentation](https://dev.europepmc.org/RestfulWebService)
distinguishes core metadata/abstracts from open-access full text and notes that
search hits are relevance ordered. We therefore verify identity explicitly.
The [provider's developer-forum guidance](https://groups.google.com/a/ebi.ac.uk/g/epmc-webservices/c/f0TIuqrmvHw)
states request-based limits of 10 per second or 500 per minute; this implementation
uses a more conservative single stream at no more than one request per second.
It does not send an email address or use a paid inference service.

The provider lock coordinates users of the same cache directory, not unrelated
programs on the same IP. Use one cache path for the campaign. Cache hits verify
stored bytes. Negative HTTP and missing-identifier responses expire; retries are
bounded and can be resumed in a new run directory after cooldown. Do not treat
HTTP 200, a DOI, a title or a matching quote as an entailment decision.

This is a bounded scientific pilot, not a calibrated autonomous reviewer or
independent inter-reviewer agreement study. Tests include paraphrase rejection,
wrong-identifier rejection, fabricated-text rehashing, citation-binding errors,
cache corruption, duplicate annotations, throttling, and no propagation of a
review to an unannotated row. Claims absent from retrieved text remain unknown;
absence from an abstract is not evidence of falsity.

The [2026-11-10 adversarial review](../validation/literature-adversarial-review-20261110.md)
records eight corrected findings and 265 passing tests. New full-text derivatives
use v2 block boundaries; old v1 full text is retained for audit but cannot produce
new quotation proofs. Original abstract quotations remain reproducible.
