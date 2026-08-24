# etalon

A known-answer recall corpus for constant-time analysers.

Every constant-time analyser a practitioner can install today prints a verdict.
None of them reports recall against a set of deployed timing leaks whose
exploitability was established independently of a tool. There is no denominator.
This is the denominator.

## What it is

Deployed timing leaks, reproduced as a vulnerable and a patched build, each
carrying a key recovery whose output verifies under the published public key.
The label on every positive item is therefore certified by arithmetic. No
analyser participates in grading itself, no expert adjudicates, and no cost
model is involved.

Against that, each installed analyser gets a measured recall per leak class,
with its `n`.

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

The instrument works end to end and has produced results. The corpus holds seven
corpus pairs and two synthetic sentinels; four pairs are recall-eligible (their
key recovery runs and verifies here), three are tier C, built and scored for
detection but with no committed recovery. Four analysers are built as
digest-pinned images: a statistical timing test, a dynamic-taint checker, the
patched Valgrind that detects variable-latency instructions, and a relational
symbolic execution engine. A fifth, a differential address-trace analyser, is
validated end to end on a pure-C address leak but its per-pair integration is
outstanding. Twelve controls pass and the oracle verifies six pairs.

Two measured findings so far. A tool-by-class matrix in which each analyser has a
different blind spot: the timing test detects both nonce classes and misses the
division-timing leak on x86, while the patched Valgrind and the symbolic engine
both detect that same leak, each by a different mechanism, and the taint checker
cannot see the variable-latency class at all; on the rejection sampler the taint
checker and the symbolic engine detect the secret-dependent branch the timing test
could not decide within budget. And a toolchain-pinning result, now measured
across two compilers and three microarchitectures: the same vulnerable source
emits a hardware division only at certain (vendor, optimisation) cells, two
compilers disagree on which, and a rented Graviton3 confirms the leak extends to
microarchitecture.

Coverage is six of eleven attested leak-class cells. The census is declared
`expanded`, not complete, so an aggregate recall figure stays gated; recall is
reported per named class with its `n`.

Corrected 2026-08-23 (UTC): this section used to say, in full, "Early. Nothing
here is a result yet." That was written at scaffold time and was true then. It
survived unchanged through the work that produced the pairs, the adapters and the
matrix above, which is the drift this correction records.

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
host, so F1 is reframed from "dudect misses a leak the others catch" to "a timing
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
