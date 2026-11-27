# Proposed preparation publication treatment — issue #238

Status: concrete coordinator proposal for independent contract review. No branch
transition, canonical removal or new publication is authorized by this document.

The actual excluded preparation canary saved and read back one engineering
RecordReview pair. Its exact bytes and source/receipt bindings must remain
immutable. The separately reviewed companion digest projection omits operational
bindings, but the original canonical pair contains them. Removing the pair from
its existing branch would violate the append-only comparison against the executed
head. That removal patch remains unapplied. The checker and its comparison base
must not be weakened to make that deletion appear valid.

The coordinator proposes a **separate source/provenance publication branch** while
retaining the executed evidence branch intact:

1. Preserve the executed branch/head
   `97c675ed3f614995d18dc3f1e8548fb83dc5cfd8`, its original canonical pair and all
   private evidence. Preserve current repaired source/tests and the original
   public files separately. Do not amend, rebase, force-push, delete the evidence
   branch or claim erasure from already-published history.
2. Publish only the reviewed helper successors, tests, bounded public digest
   views and explanatory report on a separate owned branch from the actual
   preparation base `945c421c648fe09858eabf1f2a4447ab27f9eae3`. State this base and
   the retained evidence head explicitly. The original six canonical pairs from
   that base remain byte-identical; no new canonical pair is imported, edited or
   deleted on this source/provenance branch.
3. Keep the original branch's append-only checks bound to its original history.
   The separate branch must pass normal validation against its explicitly
   declared base. Do not substitute that base when checking the old evidence
   branch, represent the digest view as a replacement RecordReview, or imply that
   the old canary executed with the repaired helpers.
4. The public report binds the actual private canonical pair and original
   command receipts by hash, and distinguishes the original run from later
   offline source repairs. The pair remains available for authorized independent
   readback in its original evidence checkout and exact private preservation.
   No actual provider call or canonical save is repeated.
5. Independently review the prospective tree, preservation mapping, all tests
   and exact published head before any claim that the new publication view is
   free of private operational bindings. Historical Git objects are explicitly
   outside that claim. No merge is requested.

This is proposed as separation of an immutable private evidence distribution from
a public engineering/provenance distribution, not an exception that permits
canonical history deletion. Independent review must specifically decide whether
the pinned publication contract permits this distinction. If it does not, retain
the hold and route a shared-owner contract decision; do not implement a local
bypass or silently relax the base.

Preservation identities:

| Original canonical artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| review.yaml | 11847 | 991f1cebaa22327283d1e54967e9b5a6a1dd8697e2e2270a88809c54f729867a |
| review.md | 18614 | 5c334713a6527ad48c8e4daf8caaa9a02b40302608152aca49f0fee282fcb2ad |

The original completed result remains metadata/abstract access plus engineering
canonical persistence only. Full text, native scientific-proof admission,
calibration, full A/B accounting, correction and resource gates remain unresolved.
This proposed publication treatment grants no scientific credit or dispatch.
