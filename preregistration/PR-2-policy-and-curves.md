# Pre-registration PR-2: policy labels, detection curves, and one new recall-eligible pair

Written before the observations it governs, and sealed in `preregistration/PR-2-SEAL.json`.
It **extends** PR-1 (`preregistration/PR-1-recall.md`); it does not supersede it. PR-1's
exploit-recall protocol, its analyser set frozen by image digest, and the results already
sealed under it are carried forward unchanged and are not re-opened here. PR-2 adds three
things that are new methodology, and fixes them before their data exists: a constant-time
**policy** label per arm and a `policy_recall` metric beside the existing `exploit_recall`;
a **detection-curve** protocol over amplification factors; and one **new recall-eligible
pair** built and scored under the same frozen analyser mappings.

## Why a second file rather than an edit

A correction or extension to a sealed pre-registration is a new file that names what it
carries forward, never an edit to the sealed one, so the predates-observations property of
each claim stays checkable. PR-1 governs exploit-recall over `dudect`, `timecop`, `varlat`,
`binsec`, `microwalk`. Nothing below changes those mappings or those numbers.

## The analyser set, carried forward

Unchanged from PR-1's frozen table (image digests in `data/tools.toml` and
`locks/images.lock.toml`; a digest change voids that analyser's rows). PR-2 adds one
declaration per analyser, `scored_against`, fixed here and not after any output is seen:

| analyser | scored_against | because |
|---|---|---|
| dudect | exploit | it measures the timing magnitude an attacker consumes, not a policy predicate |
| timecop | policy | it reports a secret-dependent branch or address, whether or not it is exploitable |
| varlat | policy | it reports a variable-latency instruction on secret operands, a policy predicate |
| binsec | policy | it decides a constant-time policy over explored paths |
| microwalk | policy | it reports a secret-dependent address, a policy predicate |

Scoring a policy tool against an exploit label converts a correct policy verdict into a
spurious "non-discriminating". That is the defect PR-2 exists to remove.

## The two labels per arm, frozen now

- **exploit_label** in {exploitable, not-exploitable}: the existing tier plus key recovery.
  Unchanged from PR-1. A vulnerable arm is exploit-labelled only where a recovery verifies
  (tier A/B) or a published recovery certifies the class (tier C, outside every denominator).
- **policy_label** in {policy-violating, policy-clean}: the presence, at a recorded source
  site, of a secret-dependent branch, a secret-indexed address, or a variable-latency
  instruction on a secret operand. Established by audit **before any tool runs**, with the
  site written into the pair manifest, so the label is not a tool's own output. A patched arm
  may be policy-violating without being exploitable: the audited site is recorded and the arm
  is labelled accordingly.

The two labels are recorded independently. Where they diverge, that divergence is a reported
finding, not an error to reconcile.

## The claims under test

- **C4, label divergence.** There exists an arm whose policy_label and exploit_label differ:
  policy-violating but not exploitable, or exploitable but policy-clean at the audited site.
  The candidate is the patched OpenSSL scalar multiplication of the nonce pairs, which timecop
  flags; PR-2 tests whether that flag is a true policy positive at a recorded site rather than
  a false alarm.
- **C5, detection is host- and magnitude-conditional.** Over amplification factors
  {1, 2, 4, 8}, dudect's samples-to-detection on a leaking arm decreases as the factor rises,
  and the KyberSlash division does **not** cross the leak band at any tested factor on the
  acquisition host, so "missed" is "not detected within budget B at magnitude m on host H"
  rather than a claim about the source.
- **C6, a new crossover with the sign reversed.** The new pair's early-exit comparison is a
  secret-dependent branch: timecop and binsec detect it (a policy detection), and dudect
  detects it (a timing detection), so the pair is a case where timecop **discriminates**,
  the opposite of its non-discrimination on the nonce pairs, and the difference is explained
  by mechanism, not by tool quality.

## The metrics, fixed now

- `exploit_recall(tool, class)` = detected / applicable over exploit-labelled pairs, with n.
  Unchanged from PR-1. Reported only for tools whose `scored_against` is exploit, and as a
  cross-reference for the others.
- `policy_recall(tool, class)` = detected / applicable over policy-labelled pairs, with n.
  New. Reported for tools whose `scored_against` is policy.
- The **cross-table**: for every arm, (exploit_label, policy_label, tool verdict), so the
  reader sees exploitable-but-policy-clean and policy-violating-but-not-exploitable cells
  directly. A tool is never scored a miss against a label it does not claim.
- No aggregate over classes. Per-class with its n, as PR-1.

## The detection-curve protocol, fixed now

- Factors {1, 2, 4, 8}, applied through the driver's amplification parameter, not by editing
  the arm. For each factor, the sample count at which dudect's |t| first crosses each band is
  recorded as `samples_to_detection`; the raw t-trajectory is committed so a re-decision needs
  no re-measurement.
- Pairs curved: the two nonce pairs, KyberSlash, the rejection sampler, and the new pair.
  Acquisition host is the one named in `results/host.json`; the curve is host-labelled and not
  comparable across hosts.
- Stopping rule per PR-1 (up to 40 batches). A factor at which no crossing occurs within budget
  is recorded as "not detected within budget", never as clean.

## The new pair, registered before it is built

- `hmac-timing`: a keyed-MAC verification whose vulnerable arm returns on the first mismatched
  byte (an early-exit `memcmp`) and whose patched arm compares in constant time. Class tuple
  (latency, message, source-level, byte, direct-recovery). Tier A: acquired and recovered here
  on x86, no lattice and no Arm.
- Recovery: the byte-by-byte timing forgery. The oracle accepts only a forged tag that equals
  `HMAC(key, msg)` recomputed under the known key (arithmetic label); the patched arm's recovery
  provably fails (`expected_patched = "not-recovered"`), two-sided per the method.
- Scored under the frozen mappings. dudect detects the timing cliff; timecop and binsec detect
  the branch; varlat is inapplicable (no variable-latency op); microwalk is inapplicable (no
  secret-indexed address). exploit_label and policy_label agree here (both violating on the
  vulnerable arm), which is the clean contrast against the nonce pairs where they diverge.

## Controls, VOID rule, consequences

- Every analyser must pass SENT-1/2 (detect the positive sentinel, stay clean on the negative)
  at the same build before any real row of this round counts. A control failure VOIDs that
  analyser's row and is neither a clean nor a miss (ported from PR-1 and null N3).
- The half-shuffle invariant must hold: relabelling the two arms with opaque tokens must change
  no verdict; a change means ground truth leaked into a container and voids the round.
- Consequences: C4 confirmed reframes timecop's nonce rows from non-discriminating to
  policy-detecting and is reported as the fairness finding. C4 refuted leaves the exploit-recall
  reading unchanged. C5 confirmed makes the KyberSlash miss host-conditional in the paper's own
  words. C6 confirmed adds the sign-reversed crossover; C6 refuted (timecop misses the branch)
  would be a defect in the harness, investigated before the pair is admitted.

## Recorded priors

- C4 (a policy/exploit divergence exists on the patched scalar mult): 0.75.
- C5 (division does not cross the band at any factor on this host; nonce pairs cross at low
  factors): 0.70.
- C6 (timecop and binsec detect the early-exit branch): 0.90.

Seal this file in `preregistration/PR-2-SEAL.json` before any policy-label scoring, any
detection-curve acquisition, or any scoring of the new pair. The sealing commit is the
timestamp of record.
