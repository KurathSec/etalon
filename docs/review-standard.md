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
`bin/paper_check.py`. Six rule kinds today:

- `[[retired]]` a withdrawn claim, which must not appear in any paper source. Matching is
  whitespace-insensitive, because LaTeX wraps and a literal substring test silently misses
  a claim split across a line break. `allow_in` names the file performing the withdrawal,
  which has to be able to quote what it retires.
- `[[ratio]]` a printed percentage, checked against its printed numerator and denominator
  read from `numbers.tex`. This is what a reader checking the arithmetic does.
- `[[forbidden]]` vocabulary refused in a named file, the anti-survey gate over the section
  carrying the analyser matrix.
- `[[once]]` a claim that must appear in exactly one file, so a limit is stated where it
  binds and nowhere else.
- `[[contradiction]]` a pair of phrases that must not both appear; the two share no wording,
  which is why the other kinds cannot see them (section 6).
- `[duplicate]` a single table, not an array: no normalised window of N words may appear in
  two paper files, with a named exemption list.

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

## 6. Before you change a claim, find everywhere it is stated

Rounds 6 to 8 taught that a fix creates the next round's finding. Round 15 taught the
specific mechanism, and it is worth naming because the protocol above did not stop it.

In one day of editing, three contradictions shipped. The abstract said the MatrixSSL
deployment link was not established while the fix section said it was no longer an
inference. A figure caption said each arm was one acquisition while the section beside it
said three, and the same caption claimed to draw no ratio while printing one. The
introduction promised three groups of non-recomputable quantities and the section it
pointed at named two. Every one was a claim updated in one place with its opposite left
standing in another. A blind referee found all three; no gate here saw any of them.

They were invisible to the existing rules by construction. `[[retired]]` looks for a
withdrawn phrase, `[duplicate]` for the same passage twice, `[[once]]` for a phrase
appearing more than once. A contradiction is none of those: the two statements are
opposites, so they share no wording, and each is individually well formed.

**The procedure, before the edit and not after it.** Enumerate every site that states the
claim: the abstract, the introduction, the section, every float caption, the conclusion,
every appendix, and the generated tables. Then choose, in this order:

1. **State it once and point at it.** Two sites cannot disagree if only one of them
   asserts. This is what the count of non-recomputable groups now does.
2. **If it must appear twice, make both print the same macro.** Two sites cannot disagree
   if the same generator fills both. This is why every quantity in this paper is a macro.
3. **If neither is possible, register the pair.** `[[contradiction]]` holds phrases that
   must not both appear. It does not detect contradiction in general and does not pretend
   to; it is a register of pairs that have contradicted once, so they cannot again.

**A caption is prose.** Two of the three shipped in captions, which are the easiest text to
forget because they are written once and read as furniture. Captions carry claims, and the
sweep covers them.

**The score is not the signal, and round 15 measured how little.** A published best paper
from this venue, lightly anonymised and put through the same panel, drew three major
revisions with five blocking items, against this paper's two majors and a minor. What the
panel's label means is therefore close to nothing. What its finding COMPOSITION means is
everything, and on that reading this paper's round 15 was worse than its round 14: the
blocking items were no longer bounded evidence, they were the paper disagreeing with
itself, in a paper whose thesis is that unreconciled numbers are false rather than weak.

## 7. Grade by consequence, and grade down when in doubt

An auditor that reports everything as blocking has not graded, it has listed, and a list
without an order is one the author has to re-read and re-grade before it can be worked. The
audit loop's convergence keys on blocking-plus-important, so inflated severity also keeps
the loop running past the point where it is finding anything worth the pass.

The rule the finders and verifiers now carry:

- **blocking**: a reader who acted on the paper would be wrong about a result, a number, or
  what was measured. The finding must name the wrong belief the reader would form. If that
  sentence cannot be written, the finding is not blocking.
- **important**: a real defect that weakens a claim or leaves a true one unsaid, but that
  changes no result and misleads nobody about what was measured.
- **minor**: everything else: wording, a missing pointer, an inconsistency with no
  consequence.

Between two levels, always the lower. Being right about a triviality does not make it
important, and the size of the prose describing a defect is not the size of the defect.

## 8. Fix in the round, then aim the next round at the fixes

A pass of the audit is followed by fixes, so the second pass is not a second sweep of the
same paper: it is a first sweep of a paper that has just been edited in ten places. It is
pointed at those places, in this order.

1. **Is the fix right?** It replaced a false statement; check the replacement against the
   source it now rests on, not against the old wording.
2. **Is it complete?** This is §6 turned into a check. A claim stated in three places and
   fixed in one is the commonest defect in a revised paper, and it is invisible to a reader
   who reads only the place that was fixed.
3. **Did it break a neighbour?** A total, a denominator or a cross-reference that agreed
   with the old wording and no longer agrees with the new one.

Only after those three does the pass look anywhere new. Broad re-sweeping is what made the
middle rounds return volume without severity.

## 9. An empty round is a result

The finders are told, from the late rounds on, that returning nothing is valid and expected.
Without that they will find something, because a lens asked what is wrong with a paper always
can be, and the cost is not neutral: every invented finding buys a verification pass and a
place on a list the author has to read and dismiss.

The evidence that this matters is the yield curve. Round 1 returned 93 confirmed findings
graded 13 blocking, 44 important, 36 minor. Round 2, after those fixes and after severity was
recalibrated by consequence, returned 37 graded 1 / 14 / 19. Round 3 returned 23 graded
0 / 10 / 13. The severity is falling faster than the count, which is what convergence looks
like from inside; a round that returned the same count at the same severity would mean the
loop had started generating its own work.

## 10. The fix is a workflow, and it is not done until a second agent finds nothing

Rounds 3 and 4 were made almost entirely of the previous round's fixes: a claim corrected at
one site while two to five siblings kept the old wording, in the paper's appendix, the README, a
docstring, the `reading` field of a results record, a pair's evidence file. Section 6 said to
find everywhere a claim is stated; a rule that is not enforced is a habit, and this one lapsed
whenever a round had fifteen fixes to make by hand.

So a fix now runs as `paperfix`, and a defect is not fixed until three things have happened:

1. **Before any edit, the whole tree is searched** for every old wording and every old number
   the defect names, and every hit is a site to correct. The search covers the paper, `bin/`,
   `results/`, `data/`, `docs/`, `README.md`, `pairs/*/evidence`, `preregistration/` and `tests/`.
2. **A generator that was edited is re-run**, so its committed record cannot contradict it, and
   a record whose generator cannot be re-run here has its prose corrected by hand to match.
   Control GEN-1 is what turns the second half into a check: every prose field of a generated
   record must appear, window by window, among its generator's string literals.
3. **A different agent tries to show the fix is incomplete**: it searches for survivors, reads
   every edited site for agreement in substance, and runs every `--check` the fix touched. A
   defect is complete only at zero survivors, and an incomplete one is retried once and then
   reported, not chased.

A fixer that disagrees with a finding says so, with the evidence path, and that is surfaced;
the one thing it may not do is skip in silence. And each round ends in one commit, so the next
round audits a committed tree and its own fixes are a `git diff` rather than a memory.
