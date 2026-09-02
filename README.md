# etalon

A recovery-certified check for whether deployed constant-time fixes hold.

A constant-time fix is a timing claim: that after the patch, the running time no
longer depends on the secret. That claim is rarely checked against the shipped code,
and a tool that prints leak or clean on one build cannot tell a fix that holds from
one that only looks like it. etalon is the instrument that can: deployed leaks
reproduced as matched vulnerable and patched builds, the recall-eligible pairs
each carrying a key recovery certified by arithmetic and the three tier-C pairs a
published recovery not rerun here, with the patched build established constant-time
at the leak site. Its headline use, pointed at three real Minerva remediations,
finds one shipped fix (MatrixSSL's, on by default) that does not hold. It doubles as a known-answer
recall corpus for the analysers themselves, the role most of the dated history below
describes.

_The sections below the status line are an append-only, dated record; the framing
above supersedes the "denominator" framing they open with (see the 2026-08-25 entry)._

## What it is

Deployed timing leaks, reproduced as a vulnerable and a patched build. Every
recall-eligible (tier A/B) pair carries a key recovery whose output verifies
under the published public key, so the label on those positive items is
certified by arithmetic; the three tier-C pairs carry a published recovery that
was not rerun here, and they enter no recall denominator. No analyser
participates in grading itself, no expert adjudicates, and no cost model is
involved.

Against that, each installed analyser gets a measured recall per leak class,
with its `n`.

## Extending it

`docs/adding-a-pair.md` is the specification: the pair manifest schema field by field,
the tool adapter interface, which control catches which mistake, and a worked example
that adds a pair from another paper by following that document and nothing else. It also
names the two mistakes that cost this project the most, timing your own scaffolding and
caricaturing the two classes, so the next person does not have to rediscover them.

## Verifying it in one command

```
sh bin/verify_all.sh        # or: make verify-all
```

runs every gate in order and prints one line per gate: `bin/verify.py` (the recovery
oracle, ORC-1/ORC-2 on every recall-eligible pair), `bin/selfcheck.py` (every control),
`python3 -m pytest -q` (the tests, which plant defects and assert the gates see them),
`bin/paper_check.py` (the manuscript rules, skipped when the untracked paper tree is
absent), and `bin/regen.py --headline`, which must refuse to print an aggregate recall
figure while the census is expanded rather than complete. That last line is the paper's
claim that the generator refuses, checked rather than asserted. Every macro the paper
prints is mapped to the emitter line and the committed record it was read from by
`bin/regen.py --provenance`, which instruments every file read during generation and
writes the eprint's provenance table.

## What it is not

Read this part before quoting any number out of it.

- **It bounds recall from below**, on the classes it contains, and says nothing
  about classes it does not contain. Coverage of the leak-class space is itself
  a reported quantity with its own `n`. A tool at 100 percent has saturated the
  corpus, not solved constant-time analysis.
- **It does not rank tools by usefulness.** Recall on historical leaks is one
  axis. A tool with lower recall and no false positives may be the better tool.
- **It measures a site-local false-positive rate, not a false-positive rate.** A
  finding inside a patched region is a genuine false positive; a finding
  elsewhere in the patched build is not, because the patched build is not
  certified constant time. A general false-positive rate needs a certified
  corpus, which is a different artifact.
- **Reproduced leaks are not leaks in the wild.** A reproduction pins a
  toolchain and a build. Every divergence from the deployed original is recorded
  per pair.

## The two halves of the oracle

Acquisition of timing observations is platform-bound and is run rarely. Some
leaks are only exploitable on hardware that a general-purpose machine does not
have. Verification is portable pure computation and runs anywhere.

```
acquisition   platform-bound, pinned   ->  recorded observations, committed
verification  portable, runs in CI     ->  observations -> key -> verifies under pk
```

Committing the observations is what makes each known answer reproducible by
anyone. Every pair declares an evidence tier: A, acquired and recovered here; B,
recovered here on published observations; C, a published exploit exists but was
not re-run. **Tier C items are listed and never enter a recall denominator**,
because the recovery was not re-run on the reproduction, so we cannot certify that
the reproduction preserved the exploitable mechanism rather than only the
instruction that carries it. The reason is reproduction drift, not circularity:
these pairs do carry published key recoveries, so their exploitability is not in
doubt; what is missing is a rerun here.

Corrected 2026-08-24 (UTC): this paragraph used to justify the tier-C exclusion as
circularity ("a corpus that labels items by 'a tool flagged it and upstream patched
it' is scoring tools against their own past output"). That was inaccurate for
KyberSlash, the rejection sampler, and the ladder leak, which all carry published
key recoveries, so the real reason is reproduction drift. The genuine circularity
the corpus does carry, varlat being the Valgrind the KyberSlash authors wrote to
catch that exact class, is now marked by construction in `data/tools.toml` and kept
out of every denominator by the tier-C rule.

## Toolchain pinning

Each pair pins vendor, version, optimisation level and target triple, and ground
truth is keyed to the resulting build. A source-only pair measures the compiler
rather than the checker. This is not packaging: it is the difference between a
corpus that measures what it claims and one that does not.

## Status

All dates in this file are UTC.

The instrument works end to end and has produced results. The corpus holds nine
corpus pairs and two synthetic sentinels; six pairs are recall-eligible (their
key recovery runs and verifies here), three are tier C, built and scored for
detection but with no committed recovery. Four analysers are built as
digest-pinned images: a statistical timing test, a dynamic-taint checker, the
patched Valgrind that detects variable-latency instructions, and a relational
symbolic execution engine. A fifth, a differential address-trace analyser, is
validated end to end on a pure-C address leak but its per-pair integration is
outstanding. Twenty-one controls pass and the oracle verifies eight pairs.

Two measured findings so far. A tool-by-class matrix in which each analyser has a
different blind spot: the timing test detects both nonce classes and misses the
division-timing leak on x86, while the patched Valgrind and the symbolic engine
both detect that same leak, each by a different mechanism, and the taint checker
cannot see the variable-latency class at all; on the rejection sampler the timing
test and the taint checker detect the secret-dependent branch, while the symbolic
engine flagged the vulnerable arm, exhausted its budget on the patched one, and is
filed inconclusive (`results/verdicts.jsonl`). And a toolchain-pinning result, now measured
across two compilers and three microarchitectures: the same vulnerable source
emits a hardware division only at certain (vendor, optimisation) cells, two
compilers disagree on which, and a rented Graviton3 confirms the leak extends to
microarchitecture.

Coverage is seven of eleven attested leak-class cells. The census is declared
`expanded`, not complete, so an aggregate recall figure stays gated; recall is
reported per named class with its `n`.

Corrected 2026-08-23 (UTC): this section used to say, in full, "Early. Nothing
here is a result yet." That was written at scaffold time and was true then. It
survived unchanged through the work that produced the pairs, the adapters and the
matrix above, which is the drift this correction records.

Corrected 2026-08-26 (UTC): every count in the section above had gone stale and none of
the earlier dated corrections had caught it, which is the drift this one records. The corpus
gained libgcrypt-minerva (tier A) and the two tier-B observation datasets, so it holds nine
corpus pairs rather than seven and six are recall-eligible rather than four; the control
suite grew from twelve to twenty-one (GEN-1, GEN-2 and FW-1 being this revision's additions)
and the oracle verifies eight pairs rather than six; and
coverage moved to seven of eleven attested cells. The counts here are the generated ones as
of that date (\nPairsCorpus, \nRecallEligible, \nControls, \nCoveredCells in
paper/tches/numbers.tex); this section is prose and not generated, which is exactly why it
drifted, and it is the last hand-maintained count of the corpus totals. The paper-structure
counts later in this file and the rule and adapter counts in docs/ are hand-maintained too,
and drift the same way.

Corrected 2026-08-24 (UTC): the analyser count above read three; a fourth, the
symbolic engine (Binsec/Rel2), is now built and scored, and the toolchain finding
gained its microarchitecture axis, so the figures in the two paragraphs above are
updated in place. A fifth analyser, a differential address-trace tool (Microwalk),
is validated end to end but not yet integrated per pair, and produces no scored
rows. The paper draft is now eighteen pages in the TCHES iacrtrans class,
findings-first: the three findings (analysers have measurable blind spots, a
constant-time label is not a property of source, the leak's magnitude is
host-dependent) are the spine, the recall corpus is the method, and three figures
generated by bin/figures.py from committed data carry the analysis. It went
through three adversarial review rounds (structure, positioning and honesty, then
consistency), whose findings were applied, and it carries a threat model, a
per-tool blind-spot matrix, a bibliography whose eighteen references are all
verified, and a number-gate test that a hand-typed figure cannot survive
regeneration.

Revised 2026-08-24 (UTC), against a third-party review. Grounding the review
against the source and data separated genuine defects from staleness. The changes
that landed: an x86 leak-presence microbenchmark (`pairs/kyberslash/x86/`,
regenerable on this host) measures the division constant-time on the acquisition
host, so I3 (the analyser index) is reframed from "dudect misses a leak the others catch" to "a timing
test reports a host-conditional truth while instruction-class tools report a
host-independent policy, and the two answer different questions"; the tier-C
exclusion is corrected from circularity to reproduction drift; the patched nonce
arms are reported at their true no-decision-band t-statistics rather than implied
clean; the nonce amplification factor is disclosed as a generated number; a dual
exploit/policy scoring (`scored_against` in `data/tools.toml`, `--recall-only` in
`bin/score.py`, PR-2 sealed) gives timecop a policy recall of one of one where its
exploit recall is zero of one; recovery cards and a divergence table are generated
from committed data (`bin/recovery_cards.py`); and the bibliography gains Magma,
LAVA, Jancar, DATA, Microwalk, ct-verif, Arm DIT and Intel DOITM. The detection
curve over amplification factors and the multi-seed recovery-success measurement
landed too: amplifying the division to 32x still surfaces no step (max |t| 11.6
against the 500 leak band), and the nonce recovery verifies on 24 of 24 random
signature subsets.

A new deployed tier-A pair was built rather than faked, against a verifiable CVE:
`hmac-timing` reproduces CVE-2013-2061, OpenVPN's non-constant-time HMAC
comparison, whose recovery forges a valid tag byte by byte from the timing and
verifies against a commitment to the true tag (ORC-1/2 both pass). All four
analysers detect it, and the taint checker DISCRIMINATES here (exploit recall one
of one) where it could not on the nonce pairs, because the OpenVPN fix deletes the
branch while the OpenSSL fix leaves a residual it still flags: its
non-discrimination is mechanism-determined, not a fixed failing. This takes tier A
from two pairs to three, recall-eligible from four to five, coverage from six of
eleven to seven of eleven (it covers the early-exit-comparison census cell), and
the recall matrix from four cells to eight across all four tools and three classes,
with varlat and binsec earning their first tier-A recall rows.

Still deliberately not faked, because both need hardware this repository does not
have: promoting KyberSlash to tier A (its recovery is exploitable only on a host
with a variable-latency divider, which this x86 host, measured constant-time, is
not), and reproducing the loud-end Cortex-A7 magnitude.

Revised 2026-08-24 (UTC), against a second third-party review, grounded against the
source before acting. The paper is now 27 pages.

dudect's decision rule was replaced. The old `[10,500]` band is not the tool's own
semantics, and the drivers stopped at the first crossing, so a banded value was a
lower bound wrongly labelled `budget_exhausted`. The runs now go to a fixed full
budget, and the verdict is the class difference of means with a bootstrap CI, decided
against a null band calibrated on the constant-time negative sentinel
(`bin/dudect_calibrate.py`) using dudect's budget-invariant `tau`. Measured, not
assumed, the consequence is that dudect flags the amplified patched nonce residual and
is non-discriminating on the nonce pairs, exactly like the taint checker: the nonce
dudect-versus-taint contrast dissolves, and the surviving crossovers are the
host-conditional division (which reads clean with an effect of a few thousandths of a
tick, CI straddling zero) and the discriminating HMAC pair. The raw samples are
committed under `results/raw/` so any reader can re-decide.

Certified constant-time negatives were added (`pairs/certified-fiat`,
`certified-fiat-add`), vendoring Fiat-Crypto's machine-checked Curve25519 field
arithmetic unmodified. All four analysers report clean on both, so the corpus now
reports a general false-positive rate (zero over these functions), separate from the
site-local count it had before. SENT-2 was made real: the negative sentinel declared
no mechanism, so no tool was applicable to it and the clean-on-the-negative claim had
no backing row; it now declares the tested mechanism and carries a binsec harness, so
all four tools score it.

Prose honesty fixes: the cross-ISA claim that instruction-class tools flag "the
identical binary" that "leaks on the Arm core" is reworded (an x86 binary does not run
on aarch64; the tools flag the x86 binary's division as a policy fact, and the same
source built for the Arm core is what leaks); the I1 emission mechanism is corrected to
the real per-compiler lowering; Simon et al. and the KyberSlash catalogue are cited;
`ecdsa-address` drops the mismatched libgcrypt CVE for its OpenSSL/Weiser DOI; the
tier-B datasets are named as observation-only with modelled patched arms. The
defensive and manifesto sentences and the abstract were trimmed per the review.

Still deliberately not done rather than faked: the recall classes remain a pilot at
`n=1`. A real recall benchmark at `n>=3` needs distinct, recovery-certified nonce
mechanisms, or from-source library builds this offline environment cannot run;
manufacturing replicate pairs would inflate `n` without establishing a rate, so the
pilot framing stands and is stated as such in the paper. The Cortex-A7 loud end still
needs hardware.

ARM phase, run 2026-08-24 (UTC) on a rented Graviton3 (Neoverse-V1, c7g.xlarge),
terminated after. It corrected the earlier Graviton finding as much as confirmed it.
Confirmed: gcc emits a hardware `udiv` at `-Os` only, committed as a real aarch64
disassembly under `locks/textprints/`, settling the open `udiv`-vs-`idiv` question (it
narrows the signed source to an unsigned `udiv` where x86 emits a signed `idiv`).
Corrected: the 0.405-tick, 5.8% signal is the udiv's operand-**magnitude** dependence,
not a step at a single-coefficient boundary; the adjacent-coefficient boundary step,
measured directly, is sub-noise. The noise floor is now derived by a committed program
(`ks_range_arm.c`, `measure_arm.py`) rather than a hand-entered constant, and the 5.8%
carries a tight CI. The W6 control: dudect run on the aarch64 build with the virtual
counter (the cycle-accurate PMU is privileged) reads the division **clean**, its tau
within the null band, because the per-call magnitude signal sits below the counter
resolution even though a batch estimator resolves 5.8%. So the statistical timing test
reads clean on both x86 and Graviton; the instruction-class tools flag the `udiv`
regardless. The tier-A recovery was attempted and is not feasible cheaply here (sub-noise
single-bit, dudect clean), so KyberSlash stays tier C with a measured reason. The paper
prose, macros, and `fig-graviton` were corrected throughout.

Recall-benchmark phase, 2026-08-24 (UTC). A real deployed-library pair was built rather
than faked: `pairs/libgcrypt-minerva` compiles libgcrypt 1.8.4 and 1.8.5 from their pinned
source tarballs (offline, checksummed in `acquire/`), signs a fixed digest on this host
under random nonces with both builds, and the vendored Minerva lattice attack recovers the
1.8.4 key (its guess reproduces that run's public key, verified here) and fails on 1.8.5.
ORC-1/2 both pass. This is the tier-A upgrade of the observation-only `minerva` pair: both
arms are measured real builds, not a modelled constant-time column, so CVE-2019-13627 is now
reproduced rather than only cited, and it is the real-library provenance the review asked
for. Tier A goes from three pairs to four, recall-eligible from five to six, corpus pairs
from eight to nine.

This corrects the note above ("from-source library builds this offline environment cannot
run"): they can, and this one did. What it does NOT do is raise the analyser recall past
`n=1`, and the reason is measured, not a shortfall. libgcrypt's Minerva fix is in its
internal ECDSA signing, where the nonce is a secure-memory scalar whose multiplication is
clamped to the field bit-length; the public `gcry_mpi_ec_mul` an installed analyser would
drive never reaches that path and leaks the scalar bit-length in BOTH 1.8.4 and 1.8.5
(measured, `acquire/record.json`). A per-arm analyser verdict on that primitive would report
a property of the public API, unchanged across the patch, not of the deployed fix, so the
pair is scored end to end by recovery (its analysers are inapplicable, exactly like the
observation datasets) and the analysers are scored on the buildable `ecdsa-nonce`
reproduction, which relocates the fix into the primitive on purpose. The real pair certifies
that the reproduced mechanism recovers a real libgcrypt key; it does not manufacture a
tool-scored replicate, so the per-class analyser recall stays `n=1` and is stated as such.

Third review, and a reframe, 2026-08-25 (UTC). A third-party review (W1-W15) grounded
against source separated genuine defects from staleness once more. The load-bearing defect
was ours: the nonce pairs' "residual" that had been read as a tool blind spot was a harness
artifact (the dudect driver timed its own BIGNUM conversion, and its classes were a
10-bit-vs-256-bit caricature). Fixed, dudect discriminates both nonce pairs (exploit recall
1/1, reversing the round-2 reading). The x86 host-index (I2) end-to-end number was confounded (two
operand classes used different constant reductions inside the timed loop; the delta fell
from 1.6% to ~0 when corrected), and the Graviton twin had the same confound. Re-measured
2026-08-25 on a fresh c7g: corrected, x86 reads ~0 (idiv with no step resolvable in a serial chain) and Graviton reads 19.1%
(delta 0.391 ticks, tight CI), a sharper contrast than the confounded 5.8%; the aarch64
dudect control reads clean with tau converging down to 0.0043 while native |t| crosses 10,
a clean validation of the budget-invariant-tau rule. Kaufmann et al. (CANS 2016) added;
timecop's capability corrected to
include address leaks; a detection can no longer rest on an unresolved patched arm; the
controls appendix is generated from selfcheck.py; host facts (P-core, DOITM) are now
regenerable.

The reframe, at the user's direction: the paper's spine moves from three findings about
analysers (now I1 to I3) to a single question the instrument is built to answer, whether a
deployed constant-time fix actually holds. Pointed at three real Minerva remediations, it
finds three outcomes. libgcrypt fixed the leak upstream of the primitive an analyser can be
pointed at. wolfSSL's fix holds, over a deployed leak its own dummy-operation balancing had
already reduced to 0.03%. (Corrected 2026-09-02 UTC: that grade was withdrawn the same day it
was written; wolfSSL is not graded, its build configuration is unrecorded and nothing was
retained, see `results/fix_verification.json`.) MatrixSSL (CVE-2019-13629) added a constant-time scalar
multiplication by default, "in response to the Minerva attack," that still sets its loop
bound from the secret nonce's digit count: the fix is incomplete, its residual measurable
(dudect tau 0.551 pre-fix to 0.123 fixed, same-length control clean) and present through the
latest open release (4.6.0). The leak carries a recoverable key; end-to-end recovery from
raw timing is host-conditional and not achieved on this fast benchmark core. MatrixSSL's
sources are an archived mirror (upstream withdrawn post-Rambus) and are marked as such.
The three index findings are demoted to supporting evidence for why a single tool verdict is not this check.
Evidence in `results/fix_verification.json` and `pairs/{libgcrypt,matrixssl}-minerva/`; new
headline section `sec/fixes.tex`.

Fourth review, 2026-08-25 (UTC). Two entries above are superseded, and both were
load-bearing claims of ours rather than reviewer misreadings. **Read this before quoting
either.**

*The MatrixSSL mechanism was wrong.* The residual was attributed to `eccMulmodCt` still
taking its loop bound from `get_digit_count(k)`. That is arithmetically impossible for the
measured design: a pstm digit is 64 bits, so a 255-bit and a 256-bit nonce occupy the same
four digits and run the identical 256 iterations. A four-design decomposition, holding the
digit count fixed while varying bit length, locates the leading-zero phase instead, whose
dummy add and double are balanced by operation count but not by cost (the dummy double is
out-of-place, forcing three big-integer copies on magnitude-variable arithmetic). `|t|`
ran 1.4 at equal length, 18 at one leading zero, 1197 at sixty-three, and 8371 once the
digit count really differs (CORRECTED 2026-08-26: those were wrong-curve figures; re-acquired
on the corrected harness they read 1.7, 17, 216 and 219, from
`results/fix_verification.json` `measurements_full_report.designs`). Pre-fix 97 to fixed 18
read as about fivefold attenuation (CORRECTED 2026-08-26: that harness timed the wrong curve,
and no attenuation ratio replaces the fivefold, because the two releases are separately built
arms and the paper's rule admits no ratio across them; the rebuild section gives the two class
differences instead). It was also reported as replicating on aarch64 (87 to 17, control 1.15);
that run predates the harness correction, so it timed a different curve, and the replication
is WITHDRAWN. The loop bound is real but
needs a nonce short by a whole digit, which a uniform nonce is 2^-64 likely to be. The
general claim is stronger than the old one: balancing control flow by operation count does
not give constant time on variable-time arithmetic.

*The verdict rule was not a valid test.* A fixed band on `tau = |t|/sqrt(n)` is not
budget-invariant under the null: `|t|` is O(1) when nothing is there, so tau falls as
n^-1/2, and the band that means `|t|=3.7` at n=40k means `|t|=59` at n=1e7. Our own
0.73-tick replicated effect sat below it. A falling tau also proves nothing, since tau
decreases with n for every effect size, so the "tau converges down, therefore null" reading
of the aarch64 control is **withdrawn**. Replaced by `bin/dudect_permute.py --assemble`: a
permutation null from each run's own committed samples, labels shuffled within batch,
absorbing dudect's 102 crops, Benjamini-Hochberg controlled across all 18 arms. It
reproduces every published verdict. The correct aarch64 reading is not detected (p=0.62)
because the effect is below one tick of `cntvct_el0`, a resolution limit rather than a
clean verdict. The uncorrected column is reported whatever it holds: an earlier revision
noted that `kyberslash_patched` carried an uncorrected p of 0.022 that BH declines; that arm
has since been re-acquired under upstream's own fix and reads p = 0.16, and no declined arm
now sits below 0.05 (the lowest is 0.11, `results/dudect_permutation.json`).

*Exploitability relabelled.* "The leak carries a recoverable key" assumed the oracle: that
lattice run was fed nonces labelled with the key it was meant to recover. MatrixSSL is now
leak-presence certified and not recovered by the published attack: nine timing-ordered
lattice attempts on the fixed build, 25,000 to 100,000 signatures at lattice dimensions 90
to 130, recover no key (`results/matrixssl_recovery.json`), and the reason is depth of
ordering, not the selection: the leak is monotone in the leading-zero count (about 2,300
ticks per zero), the fastest 90 are 5.6% contaminated on idle-host traces
(`results/exploit_budget_matrixssl_50000.json`, `_100000.json`), but the attack's rank model
credits those 90 with a mean of ~11 leading zeros where the timing order supplies ~6. The "fast host" excuse was also wrong, and
measurement refuted it: on the same host, AUC between timing and nonce shortness is 0.63
for MatrixSSL against 0.80 for libgcrypt, with the fastest 90 signatures 28.9% contaminated
against 3.3%, both from committed traces and keys
(`results/exploit_budget_matrixssl.json`; RETIRED 2026-08-27: this sentence used to quote
44.4% at a matched 6,000-signature budget and 26.7% at 250,000, from a 250,000-signature
trace that was the mislabelled 4.2.1 pre-fix build, so the matched-budget row and the
budget sweep are withdrawn, as `budget_reading_RETIRED_note` in
`results/exploit_budget.json` records). It is information content, not host noise
(`bin/exploit_budget.py`).

Also this round: every pair with a local recovery declares the channel that recovery
consumes (`class.certification_channel`), enforced by a new control CLS-6, because
`ecdsa-address` declares an address observable while its lattice runs on a co-located
timing channel, so its tier certifies the nonce bit-length and not the address trace. The
leak-class counter in `bin/build.py` matched opcodes only, so the software-division helpers
named in KyberSlash's declared class could never fire; it now matches call targets too. That change is verified to alter no committed count two ways: rebuilding every locked pair reproduces its recorded `.text` digest, and recounting the 49 committed disassemblies under both matchers gives identical numbers. The `hmac-timing` pair, which declares a required cell, turned out never to have been locked, so `BIN-2` was silently not checking it; it is built and locked now (the leak is emitted in all eight cells), and `BIN-2` now names any pair that declares a cell without a locked build instead of passing over it in silence. A new control `STAT-1` digests each committed dudect dump against the permutation row computed from it, because that record is minutes of compute and nothing regenerates it on the way to a build. `bin/build.py` also merges into the lock rather than replacing it: a `--pair` run used to write a lock containing only that pair. Amplification is stated per pair rather than in
general, and the general form was wrong: it is asymmetric on the two nonce pairs (the
loop is in the vulnerable arm only), symmetric on the HMAC and rejection pairs (the
same loop runs in both arms, widening a difference the control flow already makes), and
absent on the division pair. The `hmac-timing` and `hqc-reject` divergence notes
carried the same error and are corrected. The
fix outcomes get a taxonomy (removed, relocated, attenuated, reshaped, incomplete), the
survey's triage records all five candidates including the two not built, and the three
MatrixSSL builds are pinned by tag commit and archive digest. The paper is now 32 pages.

Closing the fourth review's remaining items, 2026-08-25 (UTC). An audit of all 44 review
items against the repository found 11 addressed, 23 partly, 8 not, and 2 excluded by
instruction (the disclosure action, and new hardware). Closing them surfaced a regression
of our own that had been shipping in clean builds.

*Coverage was wrong, and the machinery said nothing.* Adding `certification_channel` to the
`[class]` block of `pair.toml` lengthened every corpus pair's facet tuple from five keys to
six. The census attests five-facet cells, so six of nine pairs matched nothing, coverage
fell from 7 of 11 to 3 of 11, and the uncovered list grew to eight, naming cells that pairs
already cover. The paper printed 27.3% through several builds that passed every gate. The
cause is that the covered-set filter was a denylist, "every `[class]` key except two", so
any new field is silently promoted to a facet; it is now an allowlist read from the closed
vocabulary. No control caught it because `CLS-5` checks only that the coverage arithmetic is
self-consistent, and 11 - 3 = 8 is as consistent as 11 - 7 = 4. A new control `CLS-7` joins
every corpus pair to an attested census cell and fails naming any orphan; it was verified by
planting a facet break and watching it fire. Coverage is 7 of 11 again, corroborated by the
review's own reference to four uncovered cells.

*Exploitability is now measured rather than argued.* `results/exploit_budget.json` records,
on the same host and estimator, an AUC between signing time and nonce shortness of 0.63 for
the MatrixSSL residual against 0.80 for the libgcrypt leak that does yield, with the fastest
90 signatures 28.9% contaminated against 3.3% (CORRECTED 2026-08-26: this paragraph used to
quote 44% at a matched budget improving only to 27% at a forty-fold larger budget; both
figures came from an uncommitted 250,000-signature trace that was the 4.2.1 pre-fix build,
so the matched-budget row and the budget sweep are withdrawn and the contamination is now
read from the committed 25,000-signature 4-3-0 trace and key, see `_correction` in that
record). That is what the committed 25,000-signature trace's contamination means quantitatively,
and the quiet-host traces show most of it was the acquisition rather than the residual. Getting there required
catching a key/trace mismatch: pairing the committed 4-3-0 key with the 4-2-1 trace gives
an AUC of 0.5047, which is the signature of random labels rather than a finding. The
libgcrypt key is not assumed; it is what that pair's own committed recovery returns. The retracted claims are out of `results/fix_verification.json`, the acquisition
script and the evidence note, which had all kept the loop-bound attribution and the
"host-conditional" excuse after the paper dropped them.

*Registered rather than narrated.* `preregistration/PR-4-permutation-verdict.md` registers
the permutation rule and records the deviations this round created: that PR-3's band was
applied before being retired, that its prediction C7 was falsified by the harness fix, and
that PR-2's five-pair detection curve remained unrun and still rested on the retired band
(since discharged: the curve has been run, and the seal file's amendment records it).

Also: policy recall renamed to policy detection and always paired with the patched-arm alarm
count (3 of 9 for the taint checker); dudect's crop ladder, its excluded second-order test,
and both counter frequencies stated so ticks convert to cycles; and coverage bracketed across
facet granularities, 56% to 70% around the 63.6% point value, which is the disagreement that
exposed the regression above.

The last of the fourth review's items, 2026-08-25 (UTC). Two remained: the five-pair
detection curve this project registered in advance and had never run, and a
certified-negative set too small to support the false-positive rate it fed. Both are
closed, and both went against us.

*The registered curve falsifies a registered expectation.* Each pair's amplification was
compiled into its arms, which is why the curve had gone unrun for two revisions; each now
guards its constant with `#ifndef AMP`, so the factor is a build-time parameter and the
default build is byte-identical to what was committed. Run over all five pairs at factors
one through eight, on both arms, decided by permutation: **four of the five already
discriminate at factor one**, each rejecting its null on the vulnerable arm while its
patched arm reads clean (patched-arm permutation |t| 1.6, 1.6, 1.9, 1.7; p 0.65, 0.75,
0.87, 0.33; `results/detection_curve_all.json`, `pairs_discriminating_at_factor_one`). On
the vulnerable arms the nonce pairs read |t| = 17 unamplified, the message pair 220, the
rejection sampler 165. The amplification those pairs carry is therefore not what
earns their detections, and the caveat this work has been repeating, that a detection is
earned at an amplitude we chose, is weaker than we had stated it. The shapes also separate
three behaviours a single factor hides: the nonce pairs grow with gain (17 to 59,
asymmetric amplification of a real effect), the rejection sampler is flat (165 to 165,
symmetric amplification scaling signal and noise together), and the message pair climbs
steeply (220 to 1901, symmetric but against a fixed overhead). The division stays null
across the range, corroborating the separate paired sweep by an independent route.

*The prior-work comparison was wrong in our favour, twice.* Sweeping the libgcrypt pair to
its boundary gives N*(p=1) = 6000 signatures and N*(p=0.5) = 3000, against the 1200 Minerva
reports for real cryptographic library data: we are five times less efficient on the same
kind of target. An earlier entry in this file claimed a factor under two, by comparing
their real-library result against our amplified reproduction, which needs 2000. The
amplified pair is cheaper precisely because it is amplified, so that was never the
like-for-like comparison. It is printed the unflattering way now.

*The certified-negative set is doubled*, from the general multiply and the add/sub/carry
chain to include the squaring path and serialisation, the last chosen because it is the
shape most likely to draw a spurious flag from an address-sensitive checker. Four pairs by
four analysers, sixteen scorings, zero false positives.

One control earned its place in the process. Adding those two pairs committed four new raw
dumps and left the permutation record describing only the previous eighteen; every other
gate passed, and `STAT-1` failed and named the four files. Nothing else in the repository
cross-checks that record against the samples on disk.

A control for the class of error this round kept producing, 2026-08-25 (UTC). Several
defects found while closing the fourth review shared one structure, and it is worth a
mechanism rather than a warning.

For a measurement that seeks a null, an instrument that fails produces the same
observation as the result being sought. A profiler whose binary never loaded reports
identical instruction counts between two classes, which reads as "the difference is
microarchitectural rather than algorithmic". A consistency check that iterates a field its
input does not carry reports no discrepancies. A correlation computed against a mismatched
key returns an AUC of one half, which reads as "the timing carries no information". An
instruction counter pointed at a caller whose callee was not inlined reports a
division-free build. Every one of those is a clean reading, and this corpus's findings are
largely clean readings, so nothing downstream has cause to question one. There is a
second, harder variant: a failure that produces the result which merely looks
conservative. The census join broke and coverage fell, and this repository's own prose
calls a falling coverage "the honest direction".

The corpus already had the answer and was applying it in one direction only. `SENT-1` and
`SENT-2` void an analyser's rows unless it detects a planted leak and stays clean on a
certified one, at the same build and invocation. `INST-1` turns that inward: every
instrument the corpus reports through is now exercised on two committed inputs whose
answers are known, one loud and one quiet. The permutation null must reject the planted
sentinel and must not reject the certified-clean arm; the leak-class counter must find a
division in a cell recorded as emitting one and none in a cell recorded as emitting none;
the information measure must see a planted association between timing and a secret bit and
must not see one once the labels are shuffled. A one-sided check cannot catch this class,
because the failure is the quiet side.

`META-1` enforces a rule this file has stated since it was written and never checked: no
control may report a pass having examined nothing. The suite now inspects its own results
and fails if any pass is hollow. Seventeen controls, and both new ones were verified by
planting a failure rather than by watching them pass.

One detail worth keeping. `FW-1`, the vocabulary firewall, rejected the new control's own
docstring for a reserved cross-repository term. The firewall stores digests rather than
plaintext, so the hit was located by hashing the line's n-grams and reporting only its
shape, never the word. A control caught the controls, because it was watching a property
their author was not thinking about, which is the same reason `META-1` inspects results
rather than trusting each control's self-report.

Blind panel review, 2026-08-25 (UTC). A second review process was built alongside the
grounded one and is kept because the two find different things. Three referees and an
action editor read the rendered submission and nothing else: no repository, no data, no
prior rounds, no sight of one another. A grounded reviewer catches numbers that disagree
with their source. A blind referee catches what a reader catches, which is a claim the
paper does not carry, an argument whose steps do not connect, and a contribution that
cannot be restated from the text. Only the blind reviewer is in the reader's position.

The process is `~/.claude/workflows/blindpanel.js`. Regenerate the submission from the
built PDF before each round and check that no source is newer than it; the first run
reviewed a stale document and the round was wasted.

*What it found that the grounded review had not.* Round 1: we were grading wolfSSL
although our own two-sided oracle forbids it. That oracle requires the recovery to
succeed on the vulnerable arm and fail on the patched one; for wolfSSL it succeeds on
neither, so the instrument never demonstrated the bug and cannot certify its removal.
The verdict is withdrawn, and the fix taxonomy's `attenuated` cell is now empty, because
the attenuation that case exhibits belongs to the pre-fix build one release before the
patch under test. Two decided cases and one out of the method's reach is the honest
count, and the boundary is worth more than the grade: fix verification as defined here
needs an exploitable vulnerable arm, so a leak the vendor already closed falls outside it.

Round 1 also forced the headline to be reported to the standard the paper imposes on
everything else, and that changed the numbers. The recorded values were dudect's own
printed maximum, which includes the second-order test the permutation null excludes: on
the acquisition then in force the pre-fix design read 79 rather than 97, the fixed design
15 rather than 18, the same-digit design 213 rather than 1197. All of those predate the
harness correction of 2026-08-26; the values now in force are the post-correction
re-acquisition in `measurements_full_report.designs`. Reporting effect sizes alongside makes the
mechanism argument stronger, not weaker: by the statistic the same-digit and
different-digit designs are indistinguishable (213 against 218), while in ticks they are
148,176 against 901,716. The statistic saturates; the difference in ticks keeps scaling
with the work each design changes. That is the case for the reporting rule, made against
our own headline.

Round 2 found the wolfSSL withdrawal left standing in three other sections, the third
time in this cycle that a corrected claim was not swept. `bin/paper_check.py` now reads
each case's committed outcome and fails on any prose that grades a withdrawn one.
Building that guard exposed a worse one: the identity scan had been globbing
`paper/tches/*.tex` and never reading `sec/`, so every anonymity pass on a double-blind
submission had been checking about a twentieth of the paper.

Five blind-panel rounds, complete, 2026-08-25 (UTC). Three independent referees and an
action editor, each round against a freshly rendered submission and nothing else.
Recommendations went 3x major, 3x major, 3x major, then two referees at minor, then one,
with the editor closing at "major revision at the light end".

The panel never found an arithmetic error. The grounded review had already cleared those,
and all three referees checked the internal arithmetic each round and reported it
consistent. What the panel found instead, every single round, was one thing: the paper
failing to hold itself to a rule it states. It graded a case its own two-sided oracle
forbids. It reported its headline below the standard it demands of every other arm. It
merged, in its own summary table, the two axes it argues must be kept apart. It stated a
reproducibility guarantee without its one exception. It shipped a control whose written
predicate would have voided the paper's own policy-versus-exploit finding. It omitted the
attack model from the table although its own task formulation makes that index mandatory.
And it wrote an admission rule that, as phrased, forbade the most consequential outcome
the method could report.

None of that is visible to a reviewer checking numbers against data, because each number
was right. What was wrong was the licence to state the claim, and only a reader who has
the paper and nothing else is positioned to notice.

The last round's most serious finding was an error introduced two rounds earlier while
correcting a different one. The cost of one leading zero was printed as 1,436
instructions, which is 90,449 divided by 63: the sixty-three-zero average presented as the
one-zero figure, against the 37,382 the same section gives two paragraphs later. The
corrected shape is better evidence than the wrong one, and it was corrected AGAIN after the
harness rebuild, which is the point. Those counts, 37,382 and 90,449, came from the driver
that passed a zeroed curve coefficient where the library passes NULL, so they timed a
different curve. Per call, on the corrected driver, one leading zero saves 53,157
instructions and sixty-three save 53,696 (`results/matrixssl_icount.json`): the same figure
to within 1.0%, so the count is FLAT in the number of zeros rather than sublinear in it. That is the
stronger reading and the one the paper now makes: the dummy add and double balance the
operation count, and the clock moves by nearly two orders of magnitude anyway, which is
precisely why an instruction count cannot stand in for cost. The lesson worth carrying is
that correcting a claim is exactly when a new wrong number enters the same paragraph, and
this paragraph proved it twice.


## Cutting the main body to nineteen pages

The paper had grown to 41 pages, and most of the growth was defensive. Because every
scored pair is a reproduction rather than a wild binary, each result had accumulated its
own hedge, and the hedges had started to outweigh what they qualified. The revision moves
the machinery behind the findings out of the body and leaves the findings in it.

As of 2026-08-26, before the restructure and the house-form rebuild recorded below, the main
body was seven sections over 19 pages: introduction, background,
the three deployed fixes, the certified ground truth, one section carrying the three index findings
as subsections, the limits, and the conclusion. They were three separate sections
before; merging them keeps their `sec:blindspots`, `sec:toolchain` and `sec:microarch`
labels alive as subsection labels, so every cross-reference in the paper still resolves
without being rewritten. The recall corpus section became Appendix C, and the takeaway
section folded into the conclusion. (None of those counts describes the tree now: the body
has nine sections including the indexing section, the three index sections are back at
section level under the same labels and titled I1 to I3 in reading order (the earlier letter labels
were never defined and ran against that order), the corpus section sits in Appendix A, the eprint build carries six
appendices, and the body ends on page 20; see the house-form entry below.)

At that date six appendices, lettered A to F, carried what a reader consults rather than
reads: the glossary and capability table with the applicability accounting and the verdict
semantics (A), the statistical rule in full with the retired bands, the registration
deviations and both amplification sweeps (B), the corpus inventory, census, recovery cards
and cost (C), the emission control, flag sweep, in-context check and the three
per-operation quantities per host (D), the remaining limits including the harness artifact
this work had to correct (E), and the control table (F). The eprint build now carries six
(`paper/tches/main-eprint.tex`: app-defs, app-stats, app-measure, app-threats, ep-limits,
ep-related),
with the corpus inventory folded into Appendix A beside the glossary and the control table
folded into the further-limits appendix. Four floats moved with them: the blind-spot figure, which
duplicated the outcome table it sat beside, the detection-curve figure, the glossary and
the capability table.

What was cut rather than moved was self-commentary: sentences that graded the paper's own
honesty instead of reporting a result. The failure-class contribution stays, because it is
a contribution. `INST-1` and `META-1` are still stated in the body as a general claim,
that for a measurement seeking a null an instrument that fails produces the same
observation as the result being sought, with the two-sided instrument sentinels that close
it. What went is the surrounding apology.

At that date the paper built at 34 pages, 19 of main body, references on 20 and 21,
appendices from 22; the tree now builds twice, the submission ending its body on page 20 and
the eprint its content on page 34. All 18 controls pass, the 14 tests pass, and `paper_check` and `namecheck` are clean.

## Thirteen rounds of blind review, and the standard that came out of it

Rounds 1 to 5 converged: three major recommendations down to "major revision at the light
end". Rounds 6 to 8 did not. All three were three-major, and the reason was visible in the
findings rather than the scores: a large share of each round's blocking items were defects
introduced by the previous round's fixes. Round 8 named six internal collisions and three
were ours from round 7, including a claim withdrawn in the body while a verbatim copy
survived in an appendix. The body meanwhile grew from 19 to 21 pages of increasingly
self-referential caveats, and the caveats were what the next round searched.

`docs/review-standard.md` is the protocol that replaced the loop. Findings are classified
before anything is fixed: inconsistency, overclaim, obtainable gap, unobtainable gap,
structural fact. The last two are re-raised every round because the panel is blind and has
no memory, and they are stated once and never re-litigated. Inconsistencies are never fixed
by hand alone: each gets a declarative rule in `data/paper_consistency.toml`, enforced by
`bin/paper_check.py`, with `[[retired]]` claims that must not reappear and `[[ratio]]`
percentages recomputed from their macros. The first version of that check passed over the
real defect because the claim was split across a line break; whitespace-insensitive matching
fixed it, and there is a planted-failure test.

What the later rounds actually bought, none of it a caveat:

- **The containment arithmetic, and then its resolution.** 42,633,192 retired instructions
  cannot fit inside a 1,015,936-tick signature; that needs 42 instructions per counter tick.
  The paper reported the three figures as mutually impossible with the culprit undetermined,
  and that stood until the rebuild. It was our own harness: the dudect driver passed a
  freshly allocated zero as `eccMulmod`'s last argument, which is the curve's `a`
  coefficient, where the deployed call passes NULL, so it timed scalar multiplication on a
  different curve at 3.46x the cost of the deployed call (3.42x the library's own key
  generation). Measured together in one interleaved process the
  isolated call and the library's own key generation agree to 1.03%, and the corrected call
  retires about
  9.62 million instructions in about 1.6 million ticks. There is no anomaly left to report.
- **A power column.** Every patched arm now carries its class difference and CI half-width.
  The division's patched arm resolves to 0.022 ticks, so that measurement would have caught
  an effect an order of magnitude larger than the 0.001-tick step present there.
- **BIN-1 run and recorded.** 80 binaries rebuilt to their recorded `.text` digest, zero
  drift, written to `results/bin1_check.json` and given its own "on demand" status.
- **Two real bugs in our own tools.** `bin/dudect_ci.py` never decompressed, so on the only
  form the artifact commits it parsed gzip containers as records. INST-1's information
  measure tested a re-implemented AUC instead of the script that produces the numbers.
- **The nonce draw schedule**, which a referee asked for and the harness already got right:
  redrawn per measurement with only the top byte fixed, so the residual is a difference
  between distributions and not between two values.

The title now reads *a default-on Minerva fix whose site is still open*, which is what the
evidence carries. Every figure that cannot be recomputed from committed samples is marked on
the page.

## Restructured around one thesis

Thirteen blind-review rounds put the paper at major revision and held it there for a reason
that turned out to be countable. **30 of 33 blocking items (91%) attached to the MatrixSSL
fix case. Zero ever attached to the emission map or to the task formulation,** the two
things every referee from round 9 on named as the contribution. The paper was spending 11 of
26 body pages on its weakest-evidenced asset and about 2 on its strongest.

The paper is now organised around the claim that unifies what it already measured: **a
constant-time claim is meaningless unless it is indexed, and it needs an arbiter that is not
a tool.** The label is indexed by the build cell, by the host, and by what an analyser can
observe at what budget; a fix's status is indexed by site, secret facet, attack model and
budget. Stated with a quantifier rather than as a truism: the index changes the answer, and
by how much.

Three consequences of the reordering are worth recording, because they were latent in the old
structure and invisible:

- **libgcrypt stopped being a non-result.** The same patch is closed at the signing routine
  and open at the primitive a tool reaches. `sec/threats.tex` already said "every result is
  indexed by it" and filed it as a threat to validity. It is now the cleanest single instance
  of the thesis, and it leads the fix section.
- **wolfSSL's refusal became a feature.** A formulation with no domain boundary is not a
  method, so a case the admission rule declines is evidence the rule has teeth.
- **The containment anomaly became reflexive.** That the paper cannot pin its own site is,
  under the old framing, an embarrassment in a caveat. Under this one it is the paper
  applying its own rule to itself and failing the test in public.

At that date: body 26 pages to 19, ten sections; appendices six to four; total 42 pages to
35. (Superseded by the house-form rebuild below: nine body sections ending on page 20, five
appendices in the eprint build with its content ending on page 34.) An audit
found 484 of 2,063 source lines removable across 27 ranges: 34 strong self-commentary
instances, nine hedging stacks stating one limitation 3 to 6 times, two figures cited once
and zero times, and the `\nrmark` convention now marking every figure that cannot be
recomputed from committed samples.

Two mechanical changes support it. `bin/applicability_table.py` was generating a table
nothing included; it is now wired into Appendix A, and its caption had an unterminated
`\caption{` that only surfaced when something finally `\input` it. And `bin/regen.py` no
longer emits `mxAttenuation`, `mxResidualPercent*`, `mxTau*` or `icResidualPercent`: those
served claims this paper withdrew, and an emitter left behind is an invitation to quote them
again.

The restructure moved about 40% of the body text between files, which is the operation this
project's own record says goes wrong. Before any text moved, `data/paper_consistency.toml`
gained a `[[retired]]` rule per relocated claim, with `allow_in` naming the destination, so
every rule failed until its move completed and `paper_check` went green only when the last
stale copy was gone. It worked: zero stale copies survived.

### Round 14: the first minor vote in eight rounds

The restructured paper went back to the blind panel unchanged in its evidence and returned
**major, major, minor**. Thirteen rounds had returned three majors every time from round 6 on.
The editor's line is the one worth keeping: *"None of them thinks this is caveat covering a
thin result."* Nothing was measured between round 13 and round 14; what changed is which
measurement the paper leads with.

Five findings were applied.

**The KyberSlash clean reading was asserted three times and two of them were wrong.** The
paper said in three places that a direct microbenchmark measured the divider constant time on
this host "independently of any statistical test", which reads as a demonstration that no
operand dependence exists. It is not: the chained sweep finds no operand-dependent step, and a
per-call design that includes the call's surroundings resolves an effect we have not localised.
All three passages now say the narrower thing, which is that the clean verdict is consistent
with what was measured in the arrangement dudect uses.

**The Benjamini-Hochberg family is now enumerated rather than counted.** Twenty-two arms is
eleven items at two arms each, and the composition is not the obvious one: five corpus pairs
with committed dumps, four certified negatives and two synthetic sentinels. The fixtures are
inside the multiplicity family and outside every recall denominator, because multiplicity is a
property of how many tests were run and recall of which ones are scored, and the paper now says
so instead of leaving a reader to reconcile the two.

**The divergence claim was universal and its table was not.** `sec/threats.tex` said "each
pair's departures are recorded in a committed divergence block" over a table with six rows.
The claim is now scoped to the recall-eligible pairs, with the tier-C reproductions named as
absent from it and their divergences located in their manifests.

**The applicability accounting now closes on the page.** The identity was checkable only by
someone willing to hunt for the pieces; Appendix A now writes it out, and
`\Cref{tab:applicability}` names all 21 excluded rows with a reason each, so the split is
checkable row by row.

**Ten arms had been acquired twice and the paper never said so.** (CORRECTED 2026-08-26; the
paragraph as first written is wrong and the correction is below it.) The detection curve runs
each pair at amplification factor 1, and `bin/repeatability.py` compares those rows against
the committed dumps: the verdict agrees on 10 of 10.

The claim that those rows are "the default build at the committed budget", and therefore a
re-run of the same binary, is **false**, and the grounded audit caught it hours after it
shipped. The dudect adapter compiles a factor-one row with `-DAMP=1`, overriding each pair's
compiled-in constant: 40 for the ECDSA pairs, 200 for the rejection sampler, 1200 for the
message pair. Only four of the ten arms are the same binary. The committed message pair reads
-74,545 ticks against -33 on the rebuild, which should have been the tell and was not.
The effect comparison is now restricted to the three same-binary arms that also carry a
committed effect estimate, where the move is at most 1.005 ticks against a 3.485-tick
half-width. The fourth same-binary arm, the division pair's vulnerable one, has no committed
estimate to compare against, because `bin/patched_power.py` reports on patched arms only. And the two arms whose intervals had
disagreed turn out to be exactly the two whose amplification constant is shared by both arms:
the disagreement was between different binaries, not between a noisy acquisition and a quiet
one. What the ten-arm agreement supports is that the verdict turns on neither the gain nor the
run. The three same-binary arms each give one gap between two
acquisitions of one binary, at most 1.005 ticks. What they do not give is a range, which
needs more repeats and exists in this corpus only for the fix-verification case. The comparison is under control REPT-1, because a count of agreement drifts
in the reassuring direction as easily as the other one.

## Rebuilt to the venue's house form

The paper had never been checked against TCHES itself. Two research passes, over the CHES 2026
call for papers and over the eight CHES best-paper winners from 2018 to 2025, turned up a hard
constraint the project had been violating.

**The page limit counts appendices.** The call is explicit: *"up to 20 pages, including all
figures, tables, and appendices, but excluding the bibliography"*, and papers over that are
returned without review unless pre-approved. This project had been treating twenty pages as a
*body* cap with appendices free. Measured against the real rule the paper was 32 pages. The
award winners confirm the reading: every one since 2022 has zero appendices, and MIRACLE says
why in its own text, deferring its long survey to the eprint.

So there are two builds from one source tree. `main.tex` is the submission, body only, twenty
pages exactly. `main-eprint.tex` is the same body with the appendices restored.
`shared/{preamble,front,body}.tex` are inputted by both, so neither can drift. The hard rule is
that **no body paragraph is conditional**: a claim worth making appears in both PDFs and only
the pointers differ, through `\epref`, which prints a cross-reference where the appendix exists
and the place in the repository where the material lives where it does not. For a paper whose
claim is that its numbers regenerate from a cold clone, naming the generating script is a
better pointer than naming a page.

**Nine section-level changes, all from the survey of what the venue's best papers do.**

- The limitations section is gone. Two pages titled "What is not established" sat immediately
  before the conclusion; no CHES best paper arranges limitations that way. Each one now sits
  with the claim it bounds, the acquisition host and the reproduction bound open the method
  section before any number, and nothing was left over for a trailing dump.
- The conclusion is a discussion split by audience: practitioners, implementers, corpus
  authors, tool authors. Three paragraphs that were asides elsewhere are recommendations here.
- Contributions are numbered bold run-ins, each ending in a section pointer, after the CHES
  2024 winner. A `Remit.` paragraph states scope limits in the same breath, after the CHES 2022
  winner, which is the highest reviewer-defence per word in the surveyed set.
- The responsible-disclosure and artifact statements moved from page 19 to page 2.
- The abstract went from 453 words with its first number in sentence six to 295 opening on one.
- Five new floats, all generated from committed data: the four-index summary with its exact
  denominators on page 2, the code listing of the four lines the paper is about, the MatrixSSL
  four-design ladder, the five-candidate fix-survey funnel, and the field-wide analyser matrix.
- Eight new citations, all TCHES-published, all placed where they do work.

**Deliberately not done.** Numbered research questions, which are the strongest device in this
genre at CCS, USENIX and S&P and are used by no CHES best paper. The venue's form was used
instead. And no scalability column in the analyser matrix: the paper that carries one calls it
a rough estimation from the tools' own publications and devotes a limitation paragraph to why
it cannot be quantified, and inheriting a column its authors disown is the unindexed number
this paper argues against.

### Four new gates, and three of them caught something the same day

- **The page cap is a control.** `\label{endofcontent}` before the bibliography, asserted
  against the limit, refusing to pass if the label is missing, because a control that passes
  having examined nothing is a failure this corpus already has a name for.
- **Duplicated prose.** A duplicate is not a contradiction, which is why it survives every
  other rule, and it is how a claim comes to be corrected in one place and left standing in
  another. Run over the paper it found twelve, including one introduced that morning while
  fixing a round-14 finding. All twelve are gone.
- **`[[once]]` and `[[forbidden]]`.** The first makes distributing the limitations safe by
  counting them; writing it found the cold-clone claim already stated twice, eight words, under
  the duplicate rule's twelve-word window. The second refuses survey vocabulary in the section
  holding the analyser matrix, because that table classifies a field the paper did not survey.
- **Float anchoring and undefined citations.** Three of four body floats were referenced only
  from appendices and two were referenced nowhere. And a bad bibliography key renders as `[?]`
  under a LaTeX warning the reference gate did not cover; two had shipped.

Two of these gates read clean on their first run and were wrong. One used a character class
excluding per cent signs that also matched newlines, so a greedy prefix swallowed whole blocks;
the other matched `Citation \`key' undefined` where LaTeX writes `Citation \`key' on page N
undefined`. Both were caught by planting the failure, which is the rule that says a control is
decoration until you have watched it fail.

### The rebuild, and what it found in our own harness

The environment gained network access, so the MatrixSSL case was rebuilt from its pinned
checksums rather than reasoned about. All three tarballs fetch and verify, the trees build in
the pinned image, and `eccMulmodCt` is absent in 4.2.1 and present in both fixed releases,
which is the default-on claim checked rather than quoted.

**The containment anomaly was ours.** The paper had reported three figures that cannot all be
what their names say: an isolated `eccMulmod` call at 5,535,140 ticks, a whole signature
containing one at 1,015,936, and 42,633,192 retired instructions. A signature cannot be
cheaper than the scalar multiplication inside it, and which figure was wrong was left
undetermined because each came from a different harness on a different run.

The last argument of `eccMulmod` is not scratch. It is the curve's `a` coefficient, forwarded
to the projective doubling, and `ecc_curve_data.c` flags secp256r1 `isOptimized` with the
comment "1 if optimized with field parameter A=-3", so `ecc_keygen.c` never allocates it and
passes `NULL`. Our harness allocated a zeroed integer and passed that, selecting the generic
path for a different curve. Measured together in one process:

| region | median ticks |
|---|---|
| `psEccGenKey`, the signing path's own scalar multiplication | 1,615,380 |
| `eccMulmod` with the library's `NULL` argument | 1,598,670 |
| `eccMulmod` as the old harness called it, without the surrounding setup (`mulbare`) | 5,492,464 |
| whole `psEccDsaSign` | 1,763,724 |
| `eccMulmod` as the old harness called it | 5,526,240 |

The first two agree to 1.03%, so the corrected harness times the deployed call rather than a
reconstruction of it, and the deployment link stops being an inference. The old region was
3.46 times the deployed call and 3.42 times the library's own key generation.

**The finding survives and the fix looks worse.** Thirty-six acquisitions, three per design
across four designs and three releases. The residual at one leading zero is smaller in ticks
and larger as a fraction of its call, 0.07% against 0.04%, and `|t|` rises from 15 to 17
because the deployed call is quieter than the wrong one. The one-leading-zero class difference
is 1,575 ticks on 4-2-1 (between-acquisition range 155) and 1,093 on 4-3-0 (range 116), and
**no attenuation ratio is quoted between them**: the two releases are separately built arms,
which the paper's rule does not divide across, so the fivefold the old figures showed is
withdrawn rather than replaced. The latest open release is indistinguishable from
the first fixed one, and where the nonce is short by a whole 64-bit digit the fixed builds are
**twice as leaky as the pre-fix build**: the dummy operations cost more than the branch they
replaced.

**The instruction counts carry the sharper result.** Recounted on the corrected driver and
differenced across two call counts so startup cancels, one leading zero saves 53,157
instructions and sixty-three save 53,696, the same figure to within 1.0%. The clock moves over that range by
nearly two orders of magnitude. The dummy add and double balance the work exactly as designed
and do not balance the cost, which is the paper's practitioner claim turned from an argument
into a measurement. The count also fits the clock at 6.02 instructions per tick, where the old
pair of figures demanded 42, and the old count over this corrected clock would still
demand 27.

**What the rebuild retired.** Repeats replace the single acquisition every interval on this
case rested on, so between-acquisition spread is measured rather than conceded. The three
builds, the timing harness, the instruction-count driver and the signing driver are all
committed, along with 25,000 signatures, the key that labels them, and all thirty-six repeat
dumps (`results/raw/matrixssl/repeats/`, three per design and release, from which
`bin/matrixssl_report.py --check` reproduces `results/matrixssl_repeats.json`). No printed number
the paper once marked as not recomputable remains so. What still rests on uncommitted
observations is three claims, not quantities: the wolfSSL case, the key-ordered lattice run
on the pre-fix trace, and the aarch64 run that predates the harness correction; the paper
names them under "What is still not recomputable".

Corrected 2026-09-02 (UTC): the sentence above used to be current and now counts one claim
too many. The key-ordered lattice run was superseded on 2026-08-27 by nine timing-ordered
attempts on the fixed build, all recorded (`results/matrixssl_recovery.json`), so two
claims rest on uncommitted observations, the wolfSSL readings and the aarch64 run; and the
paper's paragraph is now titled "What is not recomputable".

Two generators refuse to write a result that is not there: the containment one fails if the
library's call and the corrected one differ by more than two per cent, and the instruction one
fails if the implied retire rate exceeds what a core can reach. Either would have caught the
original defect.

## The fifteenth review, and the cycle that followed

All dates UTC. A fourteen-section external review arrived after round 14. Its plan was
approved on 2026-08-27 with four decisions taken then: a declarative title, Table 2's
build/analyse/verify columns filled for all thirty-seven tools with citations, disclosure
held, and five measurements run (E1, E2, E12, E14, E15) with the rest deferred by choice.
The structural half (numbering, definitions, tables, background, references) landed as
`20cae10`.

**Five measurements.** E15: the permutation null now shuffles within the three declared
acquisition batches, read from a sidecar the adapter writes; re-deciding every committed
arm moved no verdict. E1: the KyberSlash patched arm was not upstream's fix but an
equivalent reciprocal; it is now upstream's `dda29cc` form, verified exact over the signed
range, and its re-acquired dudect arm reads p = 0.16 where the old arm's 0.02 had been the
paper's one named borderline row (PR-4 amendment 5). E14: `results/host.json` records the
frequency range during acquisition. E12: the 0.55-tick per-call effect on the acquisition
host has the high-magnitude class faster, and the identical design over the fix's reciprocal
multiply leaves 0.08 ticks, so it is the arrangement amplified by a longer instruction and
not operand-magnitude latency; at the granularity an attack consumes, one 256-coefficient
polynomial, 400,000 pairs resolve nothing to 1.93 ticks of a 1,116-tick call
(`results/kyberslash_x86_idiv.json`). E2: nine timing-ordered lattice attempts on the fixed
MatrixSSL build, 25,000 to 100,000 signatures at lattice dimensions 90 to 130, recover no
key. The reason is depth of ordering, not budget: the ladder is monotone at about 2,300
ticks per leading zero, the fastest ninety of 100,000 are 94 per cent genuinely short, but
the attack's rank model credits them with about eleven leading zeros where the timing
order supplies about six. Traces taken on an idle host select at 5.6 per cent contamination
against 28.9 on the committed trace, so host load, not the residual, had produced the
earlier figure (`results/matrixssl_recovery.json`, checked by GEN-2; the 50,000 and
100,000 signature traces and keys are committed).

**Four audit rounds, 39, 9, 9 and 1 findings.** Round two's blocking finding was
forensically real: the method section said the MatrixSSL repeat dumps carry 56,968 to
56,970 records because non-positive deltas are dropped at write time. All three hold the
full 59,967, the first byte-identical to the committed single dump, and no delta was ever
dropped; the smaller figure is the effect estimator's post-95-per-cent-crop sample size.
The record's field is now `cropped_sample_size` beside `records`, and two retired phrases
fail the build if the story returns. Round three's nine findings were all siblings of round
two's at sites a per-site fix had not reached, so it was swept by class, and it fixed a
generator defect this cycle had introduced: reading a coefficient from a C source mid-block
made the provenance table credit fourteen host macros to that source. Round four returned
one finding, the audit correcting its own round-one wording. Commits `b960235`, `6dc4965`,
`445a5d9`, `8c5b694`.

**A polish pass, and a skill.** Two passes over the prose removed self-reference about the
document, corrective narrative about earlier drafts, defensive writing, machine register
and non-structural redundancy: 2,842 words, 650 from the submission body and 2,192 from
the appendices. Three over-cuts were restored by reading the result: a limitation that
survived only in an eprint-only file, the definition of a term the abstract still used, and
a rewrite whose relative clause could attach to the wrong noun. Every gate the passes broke
traced to a rewrite and none to a cut, which is why the general skill written from it,
`paper-polish`, cuts and repairs only. A modest `\emergencystretch` in the preamble now
absorbs the line-break shifts prose edits cause.

**State on 2026-09-02.** `paper_check` clean with the content inside the twenty-page cap,
`selfcheck` 21 of 21, the tests 19 of 19, `namecheck` clean. Seven commits ahead of
`origin/main`, unpushed. Open: the blind panel has not been re-run on the rebuilt paper
since round 14; and `paper/` is gitignored, so every prose change since 2026-08-25 exists
only in the working tree, with snapshots under `cache/revision/`, which is a decision
still to take.

## The sixteenth review, and the revision against it

A third-party review arrived on 2026-09-02, written from the paper alone. Its weaknesses
were checked against the artifact before any of them was acted on, because a reader of the
paper cannot see the records: of about thirty specific claims, about twenty-two were real
and cheap to fix, three were wrong as stated, and four were structural facts the paper
should state once rather than defend (the plan under `cache/revision/` lists them). Two things the reviewer could not see were defects in our own
records: the recovery generator and its nine attempt records called the vendored Minerva
attack "error-tolerant by construction" when it tolerates no misclassification at all, and
the Graviton record said "min-of-11 batches" while the harness loops nine.

**Decisions taken with the author.** The residual gets a committed signature-budget
bound, not an error-tolerant attack: `bin/matrixssl_budget_bound.py` prints, from the
measured per-bit signal and noise under the site estimator's crop, what a
Bleichenbacher-style attack would need (SNR 0.145, an oracle error of 0.471, about 5e5
signatures at one round of reduction and 3e11 at two), and the row stays "incomplete with a
quantified bound", because Definition 5 decides residual exploitability by a recovery and a
bound is not one. wolfSSL moves to the eprint as an attempted reproduction whose samples
were not retained; the body keeps one row and one sentence saying it is not graded.
Disclosure stays held; the provenance is corroborated instead (the three tag commits in
full, their Software Heritage revisions of 2019-06-20, 2020-07-31 and 2022-12-29, the origin
snapshot of 2025-05-30), Rambus is named, and ETHICS.md gains a clause for a withdrawn
upstream. The pinned core type, cpu, part kind and free clock range are printed beside the
turbo state; a turbo-off companion run of the divider figures is prepared for the author to
run from `cache/revision/turbo-off.sh`, since it needs root for the platform switch. No
Graviton re-rent: the record holds no per-batch values, so its figure is printed as a point
estimate with no null. The prose gets a heavy polish in place rather than a rebuild.

**Phase A and B, committed as `efb4a53`.** The records and generators above; fifteen
retired wordings, two forbidden in the front matter and eleven once-only claims added to
`data/paper_consistency.toml`, each plant-tested; Table 1 with one denominator per row and
Table 5 with a key; the bibliography with page ranges added, the `lmtest` author list from
Crossref, and the VERIFY notes stripped. The build then reported what the strip had done:
BibTeX skipped two entries whose `note` field had lost its opening (`matrixsslrel`,
`binsecchanges`, "I was expecting an =") and three whose closing brace had gone with the
note (`kybercommit`, `libgcryptnews`, `wolfsslrel`, which parsed but printed no note). The
five were restored from the pre-polish snapshot, minus the VERIFY marker, and a first
attempt at the last three put two notes on the wrong entries, caught by diffing every
entry against the snapshot. The eprint PDF had been stale since the strip, because the build
stops after a BibTeX error, and DOC-1 said so.

**Locked cells (X3).** `bin/build.py` gains `-O1`, `-Oz` and `-O3 -march=x86-64-v3` for both
compilers, fourteen cells in all. The plan said `-march=native`; a locked cell must rebuild
to its digest on any host, so the portable x86-64-v3 level stands in and native stays in
the unlocked flag sweep. The map is now derived from the lock by
`bin/kyberslash_emission.py`, registered in GEN-2 and plant-tested, and its finding is
composed from the data: gcc emits the division at `-Os` and `-Oz`, clang at `-O0` and
`-Oz`, so one level is unsafe under both, which the record used to deny ("no level is
unsafe under both") because that sentence was kept by hand. The four emitting cells are
the pair's declared ground truth. BIN-1 rebuilds all 140 binaries to their digests. Figure
2 draws whatever levels the lock holds and labels each emitting cell with the divide its
textprint carries (`div` for clang at `-Oz`, `idiv` elsewhere), where it used to print
`idiv` for every one.

**The mechanism ablation (X2).** Five builds of 4.3.0 from the verified tree, differing only
inside eccMulmodCt's two dummy blocks and distinct by digest: the shipped code rebuilt the
same day; no dummy operations; the dummy double in place; evolving operands with the double
still out of place; both. `bin/matrixssl_ablate.sh` builds and times them with the site
harness under the four designs, three repeats each, pinned to the same core;
`bin/matrixssl_ablation.py` patches the source (refusing a tree without its anchors),
imports the dumps with their digests and diffs, and writes `results/matrixssl_ablation.json`
with a `--check`. The answer to the hedge the paper carried ("an ablation build that makes
the doubling in place would settle it"): a real ladder step costs 3,793 ticks and the shipped
dummy step is cheaper by 1,132, thirty per cent of a step. Making the double in place moves
the gap by 21 ticks; letting the dummy operands evolve as the ladder's do removes 1,076 of
it; with both changed 78 ticks per converted iteration remain over sixty-three iterations
and 693 over one, so the remainder is small and does not scale with the count alone. The
fixed operands account for the gap and the scratch copies are nearly free, the opposite
weighting from what a reading of the code suggested. The same-day rebuild of the shipped
code gives 71,335 ticks on the sixty-three-zero design against 71,607 committed. The paper's
hedge is replaced by the measurement and its wording retired.

**The presentation polish (Phase D).** By hand, section by section, under one mechanical rule
from the presentation assessment (kept at `cache/revision/presentation-assessment.md`): no
sentence over twenty-five words carrying more than one number, no appositive between a
subject and its verb, every term glossed or avoided at first use, cut and repair only, no
new claim, every bound kept. Each section's edits are a script under `cache/revision/`
(`polish-front.py` to `polish-rest.py`) whose every replacement asserts the text it replaces,
so the pass is replayable against the snapshot `cache/revision/polish4-baseline`. The
structural items went with it: the glossary moved from section 3 to the introduction and
now renders on page 3 beside the terms' first uses; the tick is defined in section 1; section
3 and section 6 open with what they deliver rather than a pointer; Figure 3's panels are
labelled and its caption reads by panel; Figure 4 grew from 0.30 to 0.62 of the line width
and its caption lost the sentences the body already carried; Table 6's design and
recall-refusal sentences moved from its caption into the text; I4's heading joins the "the
status is indexed by" frame and points at one section. The abstract lost its undefined
terms. The introduction's I1 paragraph was also wrong after the new cells ("clang only at
optimisation level zero") and now names `-Oz`. Two of the checker's own rules bit during the
pass, a retired wording ("of the call,") and a once-only phrase reworded by accident, and
both were restored rather than argued with. Body words by `pdftotext` before the references:
12,658 before the pass, 12,878 after the repairs, 12,770 after cutting the duplicated
related-work summary, the site-local adjudication sentence, the census sentence and the
label-kinds recap; the page gate holds at twenty pages with `paper_check` clean.

**In flight.** The turbo-off run (X1) waits on the author. Then the closing audit round,
blind panel, memory and run sheet (Phase E).
