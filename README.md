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
recall corpus for the analysers themselves, the role it was first built for.

_How this was built, review round by review round, is a dated record in
`docs/history.md`; the framing above supersedes the "denominator" framing its early
entries open with (see its 2026-08-25 entry)._

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

## Verifying it in one command

```
sh bin/verify_all.sh        # or: make verify-all
```

runs every gate in order and prints one line per gate: `bin/export.py --profile anon
--check` (the anonymous archive's residue scan, which refuses to hand over a tree where the
project name survives outside the files declared to carry it), `bin/verify.py` (the recovery
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

## Extending it

`docs/adding-a-pair.md` is the specification: the pair manifest schema field by field,
the tool adapter interface, which control catches which mistake, and a worked example
that adds a pair from another paper by following that document and nothing else. It also
names the two mistakes that cost this project the most, timing your own scaffolding and
caricaturing the two classes, so the next person does not have to rediscover them.

## Status

Dates are UTC. The counts below are hand-maintained prose and each names where it is
generated, because this section has drifted before and said so
(`docs/history.md`, the 2026-08-26 correction).

**The corpus.** Nine corpus pairs: four tier A, acquired and recovered here; two tier B,
recovered here on published observations; three tier C, carrying a published exploit that
was not rerun here, which is why they enter no recall denominator. Six are recall-eligible.
Beside them sit two synthetic sentinels and four certified constant-time negatives vendored
from Fiat-Crypto. Four analysers run as digest-pinned images: a statistical timing test, a
dynamic-taint checker, the patched Valgrind that sees variable-latency instructions, and a
relational symbolic execution engine. Coverage is seven of eleven attested leak-class cells
and the census is declared expanded rather than complete, so `bin/regen.py --headline`
refuses to print an aggregate recall and `bin/verify_all.sh` checks that it refuses.
Generated in `bin/selfcheck.py`, `results/scoring.json` and `data/census/`.

**What it has produced.** Pointed at three deployed remediations of the ECDSA nonce
bit-length leak Minerva exploited, the check returns two graded answers and one refusal.
libgcrypt's fix is closed along the deployed path and unchanged at the primitive an analyser
would be pointed at, so its site closure is *relocated*. MatrixSSL's default-on
`eccMulmodCt`, added "in response to the Minerva attack" and enabled by default, still signs
a one-bit-shorter nonce about 1,093 ticks faster over three acquisitions of 59,967
measurements, through the latest open release; an ablation of five builds locates the cause
in the dummy step's fixed operands rather than its scratch copies, and a committed bound puts
an error-tolerant recovery past every budget run here, so the site closure is *incomplete
with a quantified bound*. wolfSSL is not graded: its build configuration was not recorded and
no samples were retained. Records: `results/fix_verification.json`,
`results/matrixssl_ablation.json`, `results/matrixssl_budget_bound.json`,
`results/matrixssl_recovery.json`.

Beside that, the three indices the corpus exists to measure. The same pre-fix source emits a
hardware division in four of fourteen pinned build cells and the two compilers disagree about
which (`results/kyberslash_emission.json`). The same emitted division behaves differently on
each of three targets, a magnitude-dependent divider on one, a software routine on the
in-order core the published attack used, and no resolvable operand step on the acquisition
host (`results/kyberslash_x86_idiv.json`, `results/kyberslash_graviton.json`). And on one
binary a statistical timing test reads clean while instruction-class tools flag it, both
correct, because they assert different propositions (`results/verdicts.jsonl`).

**Gates.** Twenty-one controls, the recovery oracle over every recall-eligible pair, tests
that plant defects and assert the gates catch them, and the manuscript rules.
`bin/verify_all.sh` runs them in about nineteen minutes from a cold clone on the acquisition
host (`results/verify_all_timing.json`). CI runs the oracle, the controls, the tests and
the vocabulary firewall on every push (`.github/workflows/ci.yml`).

**The manuscript.** A TCHES submission whose body ends inside the twenty-page cap, and an
eprint build of the same tree carrying the appendices. Its prose is not in this repository:
`paper/` is gitignored, and control PAPER-1 fails the build if a file under it is ever
tracked.

**What this repository does not carry.** Two claims rest on observations it does not hold,
the wolfSSL attempt and the one aarch64 run, and so does one printed quantity, the Graviton
per-call dudect verdict. All three are named in `results/fix_verification.json`. Everything
else regenerates from committed material.

## History

`docs/history.md` is the dated record of the work: the corpus as it was built, the reviews
it went through and what each one corrected, kept append-only with every correction naming
what it used to say. It was this file's status section until 2026-09-10, when it had grown
to about a thousand lines and was moved so that the README describes the artifact rather
than its history.
