# Pre-registration PR-4: a permutation verdict rule, and the deviations from PR-2 and PR-3

Written before the re-analysis it governs, and sealed in `preregistration/PR-4-SEAL.json`.
It **extends** PR-1, PR-2 and PR-3; it does not supersede their sealed numbers. The analyser
set frozen by image digest, the exploit-recall protocol, the policy label and the two-sided
oracle are carried forward unchanged. PR-4 replaces one rule PR-3 fixed, records every
deviation from PR-2 and PR-3 that has occurred, and states which registered predictions were
falsified.

A correction to a sealed pre-registration is a new file that names what it carries forward,
never an edit to the sealed one, so the predates-observations property of each claim stays
checkable. This file follows that convention for the same reason PR-3 did.

## Why PR-3's verdict rule is replaced

PR-3 fixed a rule that decides each arm against a **null band calibrated on the negative
sentinel**, expressed on dudect's `tau = |t| / sqrt(n)`. That rule is not valid, and the
reason is arithmetic rather than a matter of taste:

- `tau` is invariant under a fixed nonzero effect, but under the null `|t|` is `O(1)`, so
  `tau` falls as `n^(-1/2)`. One constant therefore cannot serve budgets spanning
  `4e4` to `1e7`: the band that means `|t| = 3.7` at forty thousand measurements means
  `|t| = 59` at ten million.
- The cost is not hypothetical. A real, replicated per-call effect of about 0.73 ticks in
  this corpus (`|t| = 26`) has `tau = 0.013`, **below** the band, and the retired rule would
  have scored it clean.
- A corollary invalidates an argument PR-3-era prose relied on: `E[tau^2] ~ d^2/4 + 1/n`
  decreases with `n` for **every** effect size, so a falling `tau` is not evidence of a null.
  Only its asymptote separates the two, and a trajectory over budgets was never acquired.
- The band was calibrated on the sentinel harness and then applied to other harnesses, which
  assumes a noise structure the other harnesses were never shown to share.

**New rule, fixed now.** For each arm the statistic is dudect's maximum `|t|` over its
uncropped test and its 100 percentile crops (the second-order test excluded from both the
observed statistic and the null, because it accumulates against a running mean and so is not
invariant under relabelling). The null is a **permutation null built from that run's own
committed samples**: class labels are shuffled **within each measurement batch**, the crop
thresholds are held fixed, the statistic is recomputed, and
`p = (1 + #{null >= observed}) / (perms + 1)` with 10000 shuffles. A run is a **leak** iff its
`p` survives Benjamini-Hochberg control of the false discovery rate at 5% **across every
committed arm**; otherwise it is not called a leak. The class difference of means in ticks
with a bootstrap 95% CI is reported beside it as the effect size, and a run whose permutation
test does not reject while its CI straddles zero is **inconclusive**, not clean. No calibrated
band is used anywhere, and no verdict rests on a `tau` trajectory.

Guard, fixed now because it changes results: a crop whose within-class variance is zero
yields a `0/0` Welch statistic. Such crops are excluded from both the observed maximum and
the null. Without this the null degenerates, which it did on aarch64, where `cntvct_el0`
resolves the timed call to about seven ticks and 99 distinct values in 400000 measurements.

## Deviations that have occurred, recorded

- **From PR-3, the verdict rule.** PR-3's calibrated-band rule was applied to the committed
  arms before being retired. Every arm is re-decided under the rule above, from the same
  committed samples, and the record is `results/dudect_permutation.json`.
- **From PR-3, prediction C7 is falsified.** PR-3 predicted, and fixed regardless of outcome,
  that the amplified patched nonce arms would carry a residual excluding the null band, making
  dudect **non-discriminating** on the nonce pairs. They do not. The residual was an artifact
  of our own driver, which performed the `BIGNUM` conversion and reduction inside the timed
  region and compared a ten-bit scalar against a full-length one. With the conversion moved out
  and the classes set one bit apart, both patched nonce arms fail to reject their own
  permutation nulls and dudect **discriminates** on both. PR-3 fixed the rule regardless of
  outcome and named this branch explicitly, so this is the registration working.
- **From PR-2, the detection curve: DISCHARGED, and the record is corrected here.** PR-3
  recorded that the shipped curve was the division only. That commitment is now met. The
  registered five-pair curve at factors {1, 2, 4, 8} has been run
  (`results/detection_curve_all.json`), decided under the permutation rule above, on both
  arms of every pair rather than the vulnerable arm alone. The blocker was that each pair's
  amplification was compiled into its arms; each now guards its constant with `#ifndef AMP`
  so the factor is a build-time parameter and the default build is unchanged. The
  single-pair sweep was also re-run: it had been decided against the retired band, its
  generator had drifted out of sync with its own committed output, and it timed the low
  operand first on every iteration, confounding the operand with measurement order. All
  three are fixed, and it now runs five repetitions because one run of it is not
  reproducible.

  One registered prediction is falsified by the result and is recorded rather than
  quietly absorbed: the curve was registered to test whether amplification surfaces a
  leak, on the assumption that the amplified pairs need their amplification. Four of the
  five reject their null at factor one, so for those pairs the amplification is not what
  earns the detection, and the paper's standing caveat about detections being earned at a
  chosen amplitude is weaker than it had been stated.
- **From PR-3, one committed outcome is corrected under the rule PR-3 fixed.** PR-3 separated
  `inconclusive` from `clean` so that an absence of evidence is never folded into evidence of
  absence, but the scoring path applied that separation only to the vulnerable arm. A cell whose
  vulnerable arm reported a leak and whose patched arm reported `budget_exhausted` was recorded
  as a **detection**, which reads the unresolved arm as clean and so is the exact fold the rule
  forbids. The rule is now applied to both arms in one function and every committed row is
  re-derived from its committed arm statuses, running no analyser: `bin/score.py --rescore`.
  **One row of sixty changes**: binsec on `hqc-reject`, from `detected` to `inconclusive`. It is
  named here and corrected in the paper rather than quietly adopted, which is what C8 requires
  of a changed row. No recall denominator moves, because that pair is tier C.

- **From PR-4 itself, the multiplicity family grew.** C9 below is fixed over "18 committed
  arms". The family the paper reports and corrects over is 22, the row count of
  `results/dudect_permutation.json`, because two pairs gained committed dumps after this file
  was written. The prediction is unchanged in substance, at least one uncorrected `p` below
  0.05 that BH declines, and it is what happened; the denominator is recorded here so a reader
  comparing the paper's figure against the 18 above finds the reason rather than a discrepancy.
- **From PR-4 itself, the batch structure of the permutation null.** This registration says
  labels are shuffled "within each measurement batch". The implementation inferred the batch
  count from the record count and, for every 59,967-record dump, inferred nine where the
  acquisition ran three (59,967 = 9 x 6,663 = 3 x 19,989). The nine sub-blocks nested inside
  the three batches exactly, so labels stayed exchangeable within every sub-block and the
  null was valid, only finer than described; for the MatrixSSL dumps, where dropped deltas
  leave 56,968 records, the guessed blocks straddled batch boundaries. The generator now takes
  the declared count (`bin/dudect_permute.py`, `DECLARED_BATCHES`), or exact per-batch record
  counts from a sidecar the adapter writes beside every new dump. Every committed arm was
  re-decided within the three declared batches on 2026-08-27: **no verdict moved** (5 of 22
  significant at FDR 0.05 before and after); the largest change in an uncorrected p was 0.13,
  on a null arm. Recorded under C8 as a change of basis with no changed row.
- **C9's observation changed when the arm it rested on was re-acquired.** C9 fixed, before
  its observation, that at least one uncorrected `p` below 0.05 that BH declines was expected
  over the committed arms, and that any such row would be named rather than dropped. One was:
  the patched KyberSlash arm at p = 0.02. That arm has since been re-acquired, because the
  patched source was replaced by upstream's own fix (`pq-crystals/kyber` dda29cc) after a
  reviewer observed that the corpus carried a functionally equivalent reciprocal rather than
  the shipped one. On the new dump the arm reads p = 0.16, and NO declined arm now sits below
  0.05; the lowest is 0.11. The prediction is neither confirmed nor falsified, since its
  subject was rebuilt: it is recorded here as an observation that changed under a change of
  build, and the paper prints the observed floor rather than the row it used to name.
- **From PR-3, the calibration artifact.** `results/dudect_calibration.json` and
  `bin/dudect_calibrate.py` remain committed as the record of the retired rule. They are not
  read by any verdict.

## Predictions fixed now, before their observations

- **C8.** Re-deciding every committed arm under the permutation rule reproduces every verdict
  the retired band gave, so the detection-outcome matrix is unchanged and only its basis moves.
  If any verdict changes, the changed row is reported as a correction, not quietly adopted.
- **C9.** Over 18 committed arms, at least one uncorrected `p` below 0.05 that does not survive
  BH control is expected under the null. Any such row is named in the record and in the paper
  rather than dropped, and is not reported as a detection.
- **C10.** The exploitability of a residual is a budget statement, not a binary one. For each
  arm carrying a residual we report the AUC between timing and the secret facet, and the purity
  of the fastest-`k` selection the attack consumes, at a stated `n` and host. An AUC at 0.5
  certifies information loss independently of whether any particular attack converges. A
  patched arm is never described as safe on the strength of a lattice failing.

## Carried forward unchanged

The analyser set and its image digests, the applicability rule, the exploit and policy labels,
the two-sided oracle and its certification budget, the evidence tiering, and every number
already sealed under PR-1, PR-2 and PR-3.
