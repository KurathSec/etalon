# What an installable analyser can and cannot reach in this corpus

Recorded because the honest boundary is easy to cross by accident, and crossing
it produces a recall number that looks like a measurement and is not one.

## The structural fact

An installable constant-time analyser reads code: source, IR or a binary it can
run. dudect runs a program with two input classes and times it; TIMECOP runs a
program under memcheck with the secret poisoned; Binsec symbolically executes a
binary. All of them need a program.

Two of the recall-eligible pairs, Minerva and TPM-FAIL, ship recorded
observations and no program. The libgcrypt build and the STM TPM that produced
those observations are not in this repository, and one of them is a hardware
module that cannot be a program at all. So every code-running analyser is
inapplicable to them by construction. This is computed and enforced by the
applicability lattice, not asserted.

## Why a statistical detector on the traces was NOT built

It is tempting to add an adapter that reads the committed (r, s, time) triples
and reports leakage statistically, which would make dudect-style scoring
applicable to the observation-only pairs. It was considered and rejected as
dishonest, for a reason that is measured rather than argued:

A genuinely constant-time implementation still has large timing variation from
system noise. The constant-time patched arm of the positive sentinel, real
constant-time code timed by rdtsc, has a coefficient of variation of about 0.04
and nearly five thousand distinct time values over ten thousand measurements.
"The timing varies" therefore cannot distinguish leaking code from constant-time
code. A detector that fires on timing variation is a false-positive machine.

The valid test, the one dudect and Minerva both actually use, partitions
measurements by a secret-derived quantity (the nonce bit-length) and asks whether
timing differs across the partition. That quantity is not public. Computing it
needs the secret, and the only secret available here is the one the oracle
recovers, so a statistical detector built this way would be testing the timing
against an answer it already has. That is circular, and a recall number produced
from it would be a default wearing a measurement's clothes.

The patched arms of the observation pairs have their timing column set to a
constant, which models a constant-time build for the recovery's purpose. A naive
detector would "pass" on them trivially and by construction, which is exactly the
tell that the detector measures the modelling and not the code.

## The two honest routes to a recall number over deployed pairs

1. Hardware acquisition. A Raspberry Pi 2 makes the KyberSlash recovery
   reproducible, moving that pair to tier A. dudect is already applicable to its
   channel, so a real recall figure follows, and it will most likely record a
   miss on x86 and a detection on the Arm target, which is itself the finding.

2. An address-trace instrument. DATA-style differential address-trace analysis
   can reach the nonce-leakage pairs, but it needs the implementation built and
   run, not the observations. That means building libgcrypt and pointing an
   adapter at the path its fix sits in. It is real additional infrastructure and
   is recorded as the next instrument rather than faked.

Corrected 2026-08-27 (UTC). Route 2 used to read "That means vendoring and
building libgcrypt, and a different adapter family than the two built here."
Both counts are stale. libgcrypt 1.8.4 and 1.8.5 have been built and timed here
since 2026-08-24 (`pairs/libgcrypt-minerva`, tier A): the tarballs are pinned by
sha256 and fetched by the operator, not vendored, and only the timing traces are
redistributed. And the adapters built and scoring are four (dudect, TIMECOP,
varlat, Binsec), with Microwalk validated end to end but not yet scoring, so "the
two built here" was wrong on the day it was read. The gap route 2 exists to close
is still open, for a third reason distinct from the observation-only pairs, and
`results/scoring.json` (`recall_status`) records it: libgcrypt-minerva carries no
analyser row because no analyser's declared mechanism intersects the one it
exhibits. Its deployed fix sits in the secure-nonce signing path, and the public
`gcry_mpi_ec_mul` an analyser would drive leaks the scalar bit-length in both
releases (`pairs/libgcrypt-minerva/pair.toml`, class rationale). The outstanding
work is therefore an analyser that can be pointed at a signing path, not a
libgcrypt build.

Corrected 2026-08-23 (UTC). This paragraph used to read: "Until one of these
exists, the corpus reports no recall over the deployed recall-eligible pairs, and
the machinery refuses to print one. That refusal is the instrument working." That
was true when written and is now false, and the reason is worth keeping.

A third route existed that this document did not list: build a tier-A
reproduction of the leak class, so that the pair is both recovery-verified and
runnable by a code-reading analyser. That is what `ecdsa-nonce` and
`ecdsa-address` are. Per-class recall over the deployed recall-eligible pairs is
therefore reported today (see `results/recall.json`), and the two routes above
remain the way to reach the classes those pairs do not cover.

What the machinery still refuses is a single AGGREGATE recall figure, because the
census is declared `expanded` rather than a complete enumeration of the published
record. That refusal is the instrument working; the per-class numbers are not
gated and are reported.

## Binsec/Rel2: image pinned, per-pair harness outstanding

**Corrected 2026-08-24 (UTC): the harness is now built and scoring, and the two
assumptions below about how it works were wrong.** Binsec marks secrets by symbol
name in an SSE script (`secret global s`), not by address in a gdb core snapshot,
so no core is generated: a per-pair binsec driver exposes the secret and public
inputs as named globals and the tool analyses the ELF directly. It scores the
positive sentinel (insecure on the early-exit branch, secure on the patched arm),
KyberSlash (the dividend feature reports the secret-dependent division
symbolically, without measuring time, where the timing test misses it on this
x86 divider), and the rejection sampler. The image build has no gcc, so the ELF
is built in the gcc cell and analysed in the binsec cell over a shared work dir.
The two paragraphs below are kept as the pre-build record.

The official Binsec image is pulled and pinned by digest (`locks/images.lock.toml`),
and its constant-time check is `binsec -sse -checkct -checkct-features
memory-access,control-flow,divisor,dividend -sse-script SCRIPT -sse-depth D
-sse-timeout T CORE`. Two things make the per-pair harness real work, and they are
recorded rather than glossed:

1. Binsec analyses a **core snapshot**, not a source file. Each pair needs a gdb
   `generate-core-file` at the analysis entry, and the image has gdb but not gcc,
   so the binary is built in a cell and the core generated separately.
2. The secret buffers are marked symbolic in an SSE script by **address**
   (`starting from core with @[addr, n] := nondet as secret`), so the script is
   specific to each pair's memory layout.

This is the plan's own estimated multi-day item. The crossover finding the corpus
exists to show (a timing tool and a taint tool with different blind spots on the
same leak) is already established by dudect, varlat and timecop, so Binsec is a
breadth addition rather than a blocker. It is recorded here as pulled and
documented, with the per-pair snapshot harness as outstanding work, rather than
half-built.

## Microwalk: Pin works here, per-target YAML harness outstanding

**Corrected 2026-08-24 (UTC): the pipeline is now validated end to end, and the
adapter and wrapper are built; per-pair corpus integration remains outstanding.**
On a pure-C secret-indexed table access, the control-flow-leakage analysis reports
one memory-access leak in the traced target on the vulnerable arm and zero on a
branchless constant-time version, clean discrimination (`-Wl,-z,now` removes the
lazy-binding first-testcase artifact). The wrapper protocol is documented
(`PinNotifyTestcaseStart/End/StackPointer/Allocation` plus a stdin `t <id>` /
path / `e 0` loop), and `src/corpus/score/adapters/microwalk.py` runs the trace,
preprocess and analysis stages. Outstanding, and why Microwalk is not in
`data/tools.toml` and produces no scored rows: the tag-compare target hangs under
Pin, runs late in this session went flaky with a socket broken-pipe under churned
rootless podman, and the OpenSSL tier-A address target (the high-value cell) is
unbuilt. The image is pinned and Pin is confirmed working. The paragraphs below
are kept as the pre-validation record.

The flagged risk was Intel Pin's support on this Arrow Lake CPU. It does not
materialise: the pinned `ghcr.io/microwalk-project/microwalk:3.2.0-pin` image runs
Pin against `/bin/true`, enters trace-prefix mode and exits 0. So the address-trace
family is reachable on this host.

What is outstanding is Microwalk's per-target harness: a YAML pipeline
(trace / preprocess / analyse) plus a target library exposing its plugin API to
generate inputs and drive the binary. That is real integration work, comparable to
Binsec's per-pair snapshot. It is recorded as outstanding rather than half-built,
because the address-data mechanism the corpus's address pair carries is already
detected by TIMECOP (a secret-indexed access on poisoned data reports UninitValue),
so the address cell is scored today without Microwalk. Microwalk would add a second,
differential-address-trace lens on the same cell.

Added 2026-08-24 (UTC): dudect's decision rule changed (PR-3). The adapter no longer
bands `max |t|` at the pilot's `[10,500]`; the driver runs a fixed full budget (shared
`dudect_run.h`, no early stop) and dumps its raw per-measurement samples, and the
adapter reports the class difference of means with a bootstrap CI (`bin/dudect_ci.py`),
deciding leak or clean against a null band calibrated on the constant-time negative
sentinel (`bin/dudect_calibrate.py`, `results/dudect_calibration.json`) via dudect's
budget-invariant `tau`. The raw samples are committed under `results/raw/`. A new
`certified-negative` role (`pairs/certified-fiat*`) scores vendored formally-verified
constant-time code for a general false-positive rate; it is scored on the adapter
builds, carries no oracle, and `bin/verify.py` skips it.
