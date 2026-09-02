# Ethics

This repository reproduces timing side-channel vulnerabilities and ships working
key recoveries against them. That combination deserves a stated position rather
than an assumed one.

## What is in the corpus

**Every leak here is already public and already patched upstream.** A pair enters
only if it carries a CVE, a vendor advisory or a published paper, and control
CLS-4 enforces that mechanically. Nothing here discloses a vulnerability, because
there is nothing here that was not disclosed by someone else first, usually by the
researchers credited in each pair's provenance.

The corpus is drawn from the historical record, and it therefore inherits that
record's blind spots. A class the community has never found is a class the corpus
cannot contain. That is a limitation of what this measures, and it is stated in
the README rather than buried here.

## Whose keys are recovered

**Only keys generated for the purpose, or keys published by upstream for the
purpose.** Each pair's oracle verifies a recovered secret key against a public key
that is either generated from a committed seed by the pair's own harness, or taken
from the upstream artifact that published it as demonstration material. No third
party's live key is ever a target, and no recovery in this repository is pointed at
a system anyone depends on.

## If something new is found

Building a reproduction means reading deployed cryptographic code closely, and that
occasionally finds something nobody has reported. If it does:

1. It goes through coordinated disclosure with the maintainer **before** it enters
   the corpus, not after.
2. It enters only once a fix is public.
3. The pair records the disclosure timeline alongside its provenance, so a reader
   can check that the order was respected.

4. If the maintainer's channel no longer exists, because the vendor withdrew the
   repository after the tree was acquired, the finding is held rather than
   published: the tree it was found on is recorded by digest and by an archived
   location, disclosure is attempted through the successor organisation, and the
   finding is described only by its measurement until rule 2 is met or the
   successor confirms that no maintained release remains to fix. (Added
   2026-09-02: rule 1 assumed a maintainer who can be reached.)

A corpus entry is not a disclosure channel and must never become one.

## Why this is defensive work

A practitioner choosing a constant-time checker today has no basis for the choice
beyond the authors' own examples. A maintainer who runs one and gets a clean report
does not know which class of leak that report is blind to. Measuring what the
existing tools miss, against leaks the field already knows about, is what lets
those gaps be closed. The offensive content is entirely retrospective: it is the
evidence that the label on each item is true, and without it the labels would be
assertions and the recall figures would be worthless.
