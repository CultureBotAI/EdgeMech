Final read-only review of PR #59 confirmed #60/#61 fixes and found the same
parsed-byte provenance race in the downstream adjudicator. It parses annotations
before retrieval/quote verification, but hashes the annotation file only when
constructing canonical source inputs. An intervening change can produce a review
from version A while recording version B's hash; coverage then accepts B.

Capture and hash the exact annotation bytes parsed, retain that digest in the
canonical review, and recheck before publication. Add a regression that changes
annotations during retrieval or quote verification and rejects output. This P2
inherited race must be fixed for the complete annotation provenance guarantee.
