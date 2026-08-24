# Pre-registration PR-3: an effect-size verdict rule, certified-CT negatives, and a recall benchmark

Written before the observations it governs, and sealed in `preregistration/PR-3-SEAL.json`.
It **extends** PR-1 (`preregistration/PR-1-recall.md`) and PR-2
(`preregistration/PR-2-policy-and-curves.md`); it does not supersede their sealed numbers.
The analyser set frozen by image digest, the exploit-recall protocol, the policy label, and
the two-sided oracle are carried forward unchanged. PR-3 adds four things that are new
methodology and fixes them before their data exists, and records one deviation from PR-2 that
has already occurred.

## Why a third file rather than an edit

A correction or extension to a sealed pre-registration is a new file that names what it carries
forward, never an edit to the sealed one, so the predates-observations property of each claim
stays checkable. PR-1 and PR-2 govern the numbers already sealed under them; nothing below
re-opens those. The four additions all produce observations that do not exist at seal time.

## Deviation from PR-2, recorded

PR-2 registered a detection-curve protocol over factors {1, 2, 4, 8} for five pairs (the two
nonce pairs, the division, the rejection sampler, and the new pair), with `samples_to_detection`
per band and the raw t-trajectory committed. What was actually shipped was narrower: the curve
was run for the division only, at factors {1, 2, 4, 8, 16, 32}, with one scalar `|t|` per factor
and neither `samples_to_detection` nor a committed t-trajectory, and no deviation was recorded at
the time. This file records that deviation. PR-3 commits to running the PR-2 curve as registered
(five pairs, {1, 2, 4, 8}, `samples_to_detection`, committed t-trajectory) so the shipped result
matches the sealed protocol; the wider single-pair curve is kept as an additional, clearly
labelled observation, not a substitute.

## The analyser set, carried forward

Unchanged from PR-1/PR-2's frozen table (image digests in `data/tools.toml` and
`locks/images.lock.toml`; a digest change voids that analyser's rows). No mapping changes.

## The dudect verdict rule, replaced and fixed now

PR-1 decided a dudect run by band membership of `max |t|`: leak above 500, clean below 10,
no-decision between. Two facts make that rule indefensible and both are recorded here before the
re-analysis:

- The band is not the tool's own semantics. Upstream dudect returns `DUDECT_LEAKAGE_FOUND` at
  `|t| > 10` (its `t_threshold_moderate`, the same comment noting TVLA's 4.5); `[10, 500]` is not
  an "inconclusive" region of the tool but a positive-leaning one.
- The corpus drivers stop the moment dudect declares a leak (`|t| > 10`), so any committed
  `max |t|` in `[10, 500]` is a first-crossing value under optional stopping, a lower bound, not a
  budget-exhausted reading. The `budget_exhausted` label on such rows is therefore wrong.

**New rule, fixed now.** For each arm, the statistic is the class difference of means in ticks
(fixed vs random), with a bootstrap 95% confidence interval over the committed per-measurement
samples. A run is a **leak** iff its CI excludes the calibrated null band; **clean** iff the CI
lies inside it; **inconclusive** iff the CI straddles it at the budget. The null band is
**calibrated from the negative sentinel**: dudect is run on the constant-time negative sentinel
many times at the same budget, and the null band is the upper quantile of that null distribution,
not the fixed 10 or 500. The runs are re-acquired to the full budget (the early stop at `|t| > 10`
is removed) and the raw `exec_times` arrays are committed to `results/raw/`, so a later reader can
re-decide without re-measuring. A sensitivity cross-tabulation across the legacy thresholds
{4.5, 10, 500} is reported once, to show the old band's fragility, and is not the decision rule.

- **C7, the nonce contrast is threshold-dependent.** Under the effect-size + calibrated-CI rule,
  the amplified patched nonce arms carry a residual whose CI excludes the null band, so dudect is
  **non-discriminating** on the nonce pairs, like the taint checker. The rule is fixed regardless
  of outcome; if a patched arm's CI instead lies inside the null band, dudect discriminates there
  and that is reported. Either way the surviving threshold-independent crossover is the division
  (clean at every threshold on x86, `max |t|` far below 10) and the new pairs.

## Certified-CT negatives and policy precision, fixed now

- New role `certified-negative`: a small set of formally-verified constant-time functions
  (generated C from a machine-checked source), built in the pinned cells and scored by every
  applicable analyser. A finding on proven-CT code is a genuine **false positive**, unlike a
  finding on a patched arm, which is only site-local.
- **C8, a general false-positive rate exists.** `policy_precision(tool)` = 1 - (false positives /
  applicable certified-negative functions), reported per tool with its n. It is kept out of every
  recall denominator and separate from the site-local false-positive count; it is the general FPR
  the corpus previously could not report.
- A certified-negative that cannot be built in a pinned cell is recorded `blocked_by:...`, never a
  zero.

## The recall benchmark, fixed now

- New real pairs bring the latency/nonce class past n=1 tool-scored: a libgcrypt Minerva pair
  (1.8.4 vulnerable / 1.8.5 patched, two builds one upstream patch apart, real builds not a
  dataset), which also gives CVE-2019-13627 a pair that reproduces it, and one further real nonce
  pair. Each carries the full pair discipline (ORC-1/2, BIN-1/2, committed observations, portable
  recovery) and a harness for every applicable analyser.
- **C9, a per-class rate beyond existence.** For the latency/nonce class, `detection_recall` and
  `exploit_recall` (discrimination) are reported with n >= 3, so the class carries a rate, not only
  an n=1 existence claim. Any pair that cannot be built here is recorded `blocked_by:...`, not a
  zero, and the class n is reported as what was actually built.
- Class cells shared with an existing pair declare `replicate = true` and name the pair they
  replicate, so the anti-padding control is satisfied.
- No aggregate over classes. Per-class with its n, as PR-1.

## Controls, VOID rule, consequences

- Every analyser must pass SENT-1/2 (detect the positive sentinel, stay clean on the negative) at
  the same build before any real row of this round counts. The negative sentinel is made
  mechanism-bearing so that SENT-2 actually exercises each tool, rather than being vacuous. A
  control failure VOIDs that analyser's row and is neither a clean nor a miss.
- The half-shuffle invariant must hold: relabelling the two arms with opaque tokens must change no
  verdict; a change means ground truth leaked into a container and voids the round.
- Consequences: C7 confirmed removes the nonce dudect-vs-taint contrast from the paper (both tools
  non-discriminating on the amplified residual) and leaves the division and the new pairs as the
  crossovers; C7 with a clean patched CI keeps a nonce discrimination and reports it. C8 gives the
  first general false-positive number or, if a tool flags proven-CT code, a reported precision
  below one. C9 gives a per-class rate; if fewer than three nonce pairs build here, the class n is
  reported as built and the rate is labelled accordingly.

## Recorded priors

- C7 (the amplified patched nonce arms are flagged under the calibrated-CI rule): 0.75.
- C8 (at least one certified-negative builds and scores clean across all tools): 0.70.
- C9 (at least the libgcrypt Minerva pair builds, recovers, and scores here): 0.70.

Seal this file in `preregistration/PR-3-SEAL.json` before any dudect re-acquisition, any
certified-negative scoring, or any scoring of the new pairs. The sealing commit is the timestamp
of record. PR-1 and PR-2 and their sealed results are unaffected.
