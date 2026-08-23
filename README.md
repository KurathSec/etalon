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
because a corpus that labels items by "a tool flagged it and upstream patched
it" is scoring tools against their own past output.

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
rows. The paper draft is now six pages with a verified bibliography.
