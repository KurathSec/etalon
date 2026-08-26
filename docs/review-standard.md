# The review-and-fix standard

Written after blind rounds 6 to 8, because the loop stopped converging and started
generating its own work. Rounds 1 to 5 moved from three major recommendations to "major
revision at the light end". Rounds 6, 7 and 8 were all three-major, and the reason is
visible in the findings rather than in the scores: a large share of each round's blocking
items were defects introduced by the previous round's fixes. Round 8 named six collisions,
three of which were a claim corrected in the body while a stale copy survived in a table,
a caption or an appendix.

Running more rounds of the same loop makes the paper worse, not better. This is the
protocol that replaces it.

## 1. Classify every finding before fixing anything

The panel is blind and has no memory, so it re-raises structural facts every round. Those
are not defects and must not be re-fixed with new prose each time, because more prose is
more surface for the next round. Five classes, three treatments.

| Class | What it is | Treatment |
|---|---|---|
| **C1 Inconsistency** | Two places in the paper disagree; a printed ratio does not reproduce | Fix, then add a machine check so it cannot recur |
| **C2 Overclaim** | The text asserts more than the evidence carries | Scope it once, at every site, in the same edit |
| **C3 Obtainable gap** | Evidence we can produce locally | Produce it |
| **C4 Unobtainable gap** | Needs network, hardware, or a rebuild we cannot do | State once, in one designated place, and never again |
| **C5 Structural fact** | A property of the work, not the writing (n=1 per class, synthetic pairs, one measured case) | State in the abstract and introduction, then stop |

A round whose blocking items are all C4 or C5 has converged, whatever recommendation it
carries. That is the stopping rule: not "accept", which this corpus cannot reach without
experiments it cannot run, but **no open C1, C2 or C3 blocking item**.

## 2. Never fix a C1 by hand alone

Every C1 gets a rule in `data/paper_consistency.toml` and is enforced by
`bin/paper_check.py`. Two rule kinds today:

- `[[retired]]` a withdrawn claim, which must not appear in any paper source. Matching is
  whitespace-insensitive, because LaTeX wraps and a literal substring test silently misses
  a claim split across a line break. `allow_in` names the file performing the withdrawal,
  which has to be able to quote what it retires.
- `[[ratio]]` a printed percentage, checked against its printed numerator and denominator
  read from `numbers.tex`. This is what a reader checking the arithmetic does.

Plant the failure before believing the control. A rule added without seeing it fail on the
real defect is decoration.

## 3. Freeze while a round runs

Round 7 reviewed a PDF that was already three edits stale, so part of its report was spent
on text that no longer existed. The cycle is strictly:

> freeze → review → classify → fix → consistency sweep → gates → rebuild → next round

The consistency sweep is not optional and is not the same as the fix. After editing body
prose, grep the tables, captions, the abstract, the conclusion and every appendix for the
claim just changed. Most C1s are born in the gap between changing a sentence and changing
its copies.

## 4. The paper does not grow

The body is at its length limit. Any fix that adds text names what it replaces. A caveat
added without a deletion is a net loss: it enlarges the surface the next round searches,
and the last three rounds show that surface is where the findings come from.

## 5. Report composition, not score

Track blocking items by class across rounds. The recommendation label is a poor signal
because C5 findings hold it down permanently. What shows progress is C1 and C2 going to
zero and staying there.
