# Pre-registration PR-1: recall of constant-time analysers over the corpus

Written before the next scoring round, and sealed in `preregistration/SEAL.json`. It fixes,
before the observations it governs, the analyser set, the verdict mapping for each analyser,
the run budgets, what each outcome means, how recall is computed, and what follows from each
result, so that none of those can be chosen after the numbers are seen.

## Scope, and the pilot that preceded this

A first scoring run has already happened: `dudect` and `timecop` over the corpus, recorded in
`results/verdicts.jsonl` and `results/recall.json`. **That run is the exploratory pilot.** It
established the adapter contract, the applicability lattice and the verdict vocabulary, and it
is not covered by this pre-registration, because a pre-registration is written before the
observations it governs and cannot retroactively cover a run already done. This file governs
the **next** round: the analysers `varlat`, `binsec` and `microwalk` added to `dudect` and
`timecop`, over the corpus as it stands plus the pairs added this phase set (`ecdsa-address`,
`hqc`, `ladderleak`). The pilot's two findings (dudect detects the nonce leak; timecop is
non-discriminating on it) are treated as hypotheses to be re-measured under this protocol, not
as settled results.

## The claim under test

- **C1, crossover.** Over the corpus pairs and the analyser set frozen in the next section,
  there exist analysers t1 and t2 and leak classes c1 and c2 such that t1 detects c1 and not
  c2 while t2 detects c2 and not c1, with all four cells passing their controls. The pilot's
  `dudect detects / timecop non-discriminating` on the nonce class, and the predicted
  `dudect misses / varlat detects` on the division class, are the two candidate arms of C1.
- **C2, a miss exists.** At least one analyser that declares a class in scope reports clean, or
  is non-discriminating, on an exploit-certified vulnerable arm of that class.
- **C3, matched control.** For every detection, the count of analysers that also flag the
  patched arm at the same build is reported. A flag on the patched arm is a site-local false
  positive only if it localises to the patched region; elsewhere it is an unadjudicated alarm.

## The analyser set, frozen by image digest

Each analyser is pinned by container image digest and carries a verdict mapping fixed here.
The digests are recorded in `data/tools.toml` and `locks/images.lock.toml` at seal time; a
change to any digest voids that analyser's rows for this round.

| analyser | technique | detects_mechanisms | LEAK when | CLEAN when | INCONCLUSIVE when |
|---|---|---|---|---|---|
| dudect | statistical timing | secret-branch, variable-latency-op | max abs t > 500 | max abs t < 10 | 10 <= max abs t <= 500 (dudect's own bands) |
| timecop | dynamic taint | secret-branch, address-data | memcheck reports an Uninit* kind on poisoned data | no Uninit* report | valgrind error or no output |
| varlat | patched-valgrind | variable-latency-op, secret-branch | a `Variable-latency instruction operand` report on poisoned data (matched on the `what` text, not the kind) | no such report | valgrind error or no output |
| binsec | symbolic (Binsec/Rel2) | secret-branch, variable-latency-op | a feature returns `insecure` | zero insecure and the bound was exhaustive | zero insecure with `unknown`, a solver timeout, or a depth cut |
| microwalk | differential address-trace | address-data, address-code | the leakage report localises a secret-dependent access | the report is empty over the input set | Pin cannot instrument on this host, or the pipeline errors |

Deciding any of these mappings after seeing an analyser's output is the defect this section
exists to prevent. INCONCLUSIVE is never folded into CLEAN.

## Run budgets and stopping rules, fixed now

- dudect and varlat: chunk and measurement count per the pair's harness config; up to 40
  batches; the stopping rule is the threshold table above; the raw t-statistic (dudect) or the
  report set (varlat) is committed so a different threshold can re-score without re-measuring.
- binsec: `-sse-depth` and `-sse-timeout` and `-fml-solver-timeout` per the pair; a depth cut
  or timeout with zero insecure is INCONCLUSIVE, never CLEAN.
- microwalk: the input-set size fixed per pair; Pin failure on this host is INCONCLUSIVE
  reported as `blocked_by: pin_unsupported_here`, never a zero.
- Secret-input annotations and entry points are identical across the two arms of a pair.

## Controls, and the VOID rule

Each analyser must, on the two synthetic sentinels, detect the positive sentinel and not flag
the negative sentinel, at the same build and invocation mode, before its rows on any real pair
are counted (SENT-1/2). **Any control failure voids that analyser's row for that pair; it is
neither a clean nor a miss.** A round in which more than half of an analyser's rows void is a
VOID round for that analyser and is redone. No gate decision is made from a void round: "we
failed to measure" must never become "we measured nothing there".

## Scoring

recall(t, c) = detections / applicable-recall-eligible-vulnerable-arms-of-class-c, reported
with its n, NA when n is zero, never 0. Applicability is computed from the analyser's
`detects_mechanisms` against the pair's `mechanism_classes`, before any run. INCONCLUSIVE,
error, harness_failed and inapplicable are each their own count and never enter the
denominator or CLEAN. Tier C pairs never enter a denominator. Recall is reported per named
class with its n; the cross-class macro-average is available only behind a flag labelled not
an estimate of recall in the wild.

## Where the record goes

`results/verdicts.jsonl` (one row per tool, pair, arm), `results/recall.json` (per class,
with n), `results/raw/` (the committed statistics and reports). `bin/regen.py` prints every
quotable number with its n; `bin/regen.py --headline` refuses a headline figure until the
census is complete and at least four pairs are tier A or B.

## Consequences, fixed now

- **C1 holds:** the paper's headline is the tool-by-class matrix and the two blind-spot
  findings. Scaling continues.
- **C1 fails, C2 holds:** the headline is per-tool recall with the explicit statement that no
  crossover was observed at this corpus size; scaling continues, since the crossover class may
  simply be absent yet.
- **Both fail** (every in-scope analyser detects every vulnerable arm and flags no patched
  arm): the motivating premise is weaker than assumed at this corpus size; the paper is
  retitled toward corpus construction, and the four-pair decision is retaken.
- **VOID:** redo with working controls.

## Recorded priors, before the round

P(C1) = 0.80 (the pilot already shows one arm; varlat detecting the division where dudect
missed is mechanically expected). P(C2) = 0.90. P(at least one control failure somewhere) =
0.5. P(microwalk blocked by Pin on this host) = 0.4. One sentence each: C1 is near-certain
because two of its four cells are already observed or mechanically forced; the microwalk risk
is the Arrow Lake Pin support, unverified.
