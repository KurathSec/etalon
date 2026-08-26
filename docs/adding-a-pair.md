# Adding a pair, and adding a tool

This corpus is meant to be extended by people who did not build it. That needs two
things written down: what a pair manifest must contain, and what a tool adapter must
implement. Both are below, followed by a worked example that adds a pair from another
paper by following this document and nothing else.

Everything here is enforced by `bin/selfcheck.py`. If a rule below is not checked by a
control, it says so explicitly, because an unenforced rule is a suggestion.

## What a pair is

A pair is a deployed leak reproduced so that a tool can be scored on it: two builds
differing by exactly one fix at one site, plus a recovery that certifies the vulnerable
arm was exploitable. The recovery, not any analyser, is what makes the label ground
truth. A pair whose two arms differ by more than the fix is not admissible, because the
tool's verdict would then be attributable to something other than the fix.

## The manifest

One file, `pairs/<id>/pair.toml`, `schema = "pair/1"`. Blocks, in the order the existing
pairs use them:

### `[pair]`

| key | meaning |
| --- | --- |
| `id` | directory name, repeated here so the file is self-describing |
| `title` | one line, human |
| `role` | `corpus` (scored, enters denominators), `sentinel-positive` / `sentinel-negative` (fixtures, never scored), or `certified-negative` (proven constant-time, measures false positives) |
| `synthetic` | true if the arms were written here rather than taken from upstream |
| `status` | `active` or `retired` |
| `tier` | `A` acquired and recovered here, `B` recovered here on published observations, `C` published exploit not re-run here |
| `added` | ISO date |
| `summary` | what the leak is, in a few sentences |

Tier is not a quality judgement. It records what *this repository* re-executed. Tier C
pairs are scored for detection but never enter a recall denominator, because we have not
shown the reproduction preserved the exploitable mechanism rather than only the
instruction that carries it.

### `[class]`

The five facets below are a closed vocabulary defined in `data/classes.toml`. Every
value must appear there, which `CLS-1` enforces; the tuple must match an attested census
cell, which `CLS-7` enforces.

| facet | values |
| --- | --- |
| `observable` | `latency`, `address-data`, `address-code`, `cache-set`, `port-contention` |
| `secret_role` | `key-material`, `nonce`, `plaintext`, `padding-decision`, `message` |
| `origin` | `source-level`, `compiler-introduced`, `hardware-implicit`, `api-level` |
| `granularity` | `bit`, `byte`, `word`, `branch`, `whole-operation` |
| `exploit_path` | `direct-recovery`, `lattice-hnp`, `bleichenbacher`, `statistical` |

Also in this block, and **not** facets:

- `certification_channel`: the channel the pair's own recovery consumes. Required when
  `[recovery].inputs` is non-empty, checked by `CLS-6`. It is separate from `observable`
  on purpose: `ecdsa-address` declares an address observable while its lattice runs on a
  co-located timing channel, so its tier certifies the nonce bit-length and not the
  address trace. Omit it when the pair has no local recovery; do not guess.
- `mechanism_classes`: which of `secret-branch`, `address-data`, `variable-latency-op`,
  `timing-observation` the pair exhibits. This decides tool applicability before any run,
  so a tool whose mechanisms do not intersect is excluded rather than scored a miss.
- `rationale`: why these values and not the neighbouring ones.

**When adding a key to `[class]`, update every consumer that reads facets.** They take
facet names from `data/classes.toml` by allowlist precisely because an earlier field
addition was silently absorbed as a sixth facet and dropped census coverage from 7/11 to
3/11 without any control noticing.

### `[provenance]`

`provenance_kind` is one of `release-pair` (two upstream tarballs), `vendored-reproduction`
(upstream source excised verbatim), `synthetic-reproduction` (arms written here over
library primitives), or `observation-dataset` (recorded observations, no buildable arms).
It changes what a score means and is printed beside every score. Also: `upstream_repo`,
`disclosed`, `advisory`, `doi`, `licence`, `redistributable`, and a `note` recording any
caveat (a mirror rather than the vendor, a withdrawn upstream, a missing CVE).

`CLS-4` requires every corpus pair to carry a CVE, an advisory, or a DOI. A pair with
none of those is not admissible, which is also the mechanism that keeps the corpus from
becoming a disclosure channel.

### `[[build]]`, `[[site]]`, `[toolchain]`

One `[[build]]` per arm: `arm`, `source`, `entry_symbol`, `secret_input`. The two arms
must share an entry symbol and a secret-input annotation, so the fix is the only variable.

`[[site]]` names where the leak is, and `instruction_class` lists what the emission
control counts. Entries match an opcode **or a call target**, so a divide lowered to a
software helper counts; what is not listed is not counted, which is why a power-of-two
lowering to a shift does not register.

`[toolchain].cells_required` pins the build cells the pair asserts its ground truth in.
`BIN-2` checks the emission inequality in those cells and names any pair that declares a
cell it has no locked build for.

### `[recovery]` and `[oracle]`

`entry` is a script, `runtime` is `pure` (stdlib only, runs from a cold clone) or `image`.
Prefer `pure`: it is what lets a reviewer reproduce the known answer without hardware.
`inputs` lists committed observations. The oracle must be **two-sided**: succeed on the
vulnerable arm and fail on the patched arm at the same budget, which `ORC-1` and `ORC-2`
enforce. A recovery that succeeds on both is certifying its own input.

Report a budget rather than an outcome where you can: `bin/recovery_robustness.py`
sweeps subset sizes and yields N*(p), the signatures needed for success probability p.
A single success at one size says nothing about where the attack stops working.

### `[divergence]`

How the reproduction departs from the deployed original, per axis. Amplification belongs
here, and **state where it sits**: asymmetric (vulnerable arm only) or symmetric (both
arms). Symmetric amplification widens a difference the control flow already makes and
cannot create one; asymmetric amplification can. Saying only "the pair is amplified 40x"
is what let a wrong claim survive four separate places in this repository's own prose.

## The tool adapter

`src/corpus/score/adapters/<tool>.py`, exposing:

```python
def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 1800, **kw) -> dict
```

returning at least `status` and `detail`. `status` is one of:

| status | meaning |
| --- | --- |
| `leak_reported` | the tool reports a leak on this arm |
| `clean` | the tool reports no leak, and the run was valid |
| `inconclusive` | the run reached no decision |
| `error` | the run did not happen or could not be decided |

**`error` is not `clean`.** An adapter that cannot decide must say so. The dudect adapter
returns `error` when no permutation null can be built, because falling back to a
threshold is exactly how a failed measurement becomes a passing verdict.

Never trust the tool's exit code. Decide from the artifact the run produced, and commit
that artifact so a reader can re-decide without re-measuring.

Declare the tool in `data/tools.toml` under `[tool.<name>]`. The keys that decide
scoring are `detects_mechanisms` (intersected with the pair's `mechanism_classes` before
any run, so `unsupported` can never be recorded as `missed`), `observes`, `technique`,
`level`, `scored_against` (`exploit` or `policy`), `architectures`, and `image`, pinned by
digest in `locks/images.lock.toml` so a digest change voids that tool's rows.
`capability_source` cites the paper the declared capability comes from, so a capability
claim is attributable rather than assumed.

A statistical adapter reports an uncorrected per-run p; it sees one run and cannot know
the family. Multiplicity is applied in `bin/score.py`, where every arm is visible, and it
only ever downgrades.

## Worked example: adding a pair from another paper

Take a published leak with a CVE and a released fix. The steps, in order, with the
control that catches each mistake:

1. `mkdir pairs/<id>` and write `pair.toml`. Run `python3 bin/selfcheck.py`. `CLS-1`
   rejects a facet value not in the vocabulary; `CLS-7` rejects a facet tuple that
   matches no census cell, which usually means the census needs the cell added in
   `data/census/entries.jsonl` with an adjudication.
2. Write `src/vulnerable.c` and `src/patched.c` differing only at the site. If the pair
   builds under the pinned cells, run `python3 bin/build.py --pair <id>`; it merges into
   `locks/binaries.lock.json` rather than replacing it. `BIN-2` then checks the emission
   inequality per cell.
3. Write `recover/recover.py` and commit observations under `traces/`. Run
   `python3 bin/verify.py`; `ORC-1` and `ORC-2` check both sides of the oracle.
4. Write `harness/<tool>.toml` for each tool the mechanism admits, then
   `python3 bin/score.py --pair <id>`.
5. Run `python3 bin/regen.py --tex paper/tches/numbers.tex`. Any number the pair
   contributes is now a macro. `NA` in the output is the gate working: it means an
   aggregation was empty and refused to print a misleading zero.

Two failure modes worth naming in advance, because both cost this project real work:

- **Do not time your own scaffolding.** A driver that converts or reduces the secret
  inside the timed region measures the conversion, not the leak. Prepare inputs outside
  the timed region and let the timed chunk carry an index.
- **Do not caricature the classes.** Comparing a ten-bit scalar against a full-length one
  measures a distribution no attacker observes. Set the classes one unit apart at the
  granularity the pair declares.

## What is deliberately not here

The paper source lives under `paper/`, which is gitignored, so this repository carries no
prose that could identify the authors. Repository hygiene controls (`ANON-1`, `PAPER-1`,
`FW-1`) guard that boundary and the submission rather than any measurement, which is why
they are grouped apart from the measurement controls wherever both are listed.
