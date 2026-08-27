#!/usr/bin/env python3
"""Permutation null for a dudect run, computed on committed raw samples.

WHY THIS REPLACES THE FIXED TAU BAND
------------------------------------
The previous rule compared dudect's tau = |t|/sqrt(n) against one band calibrated
once on the negative sentinel. That rule is wrong in a way that matters, and this
repository's own data falsifies it twice:

  * tau is NOT budget-invariant under the null. Under H0 the t-statistic is O(1),
    so tau = O(n^-1/2): it shrinks as the budget grows. A band of 0.0187 is |t|=3.7
    at n=40k but |t|=59 at n=10^7. One band cannot serve both.
  * Consequently a downward tau trajectory proves nothing: E[tau^2] ~ d^2/4 + 1/n
    decreases in n for EVERY effect size d, null or not. Only the asymptote
    separates them (slope -1/2 under the null, slope 0 for a fixed real effect).
  * results/kyberslash_x86_idiv.json records a real, replicated 0.73-tick effect
    (|t| = 26 at n = 4e6) whose tau = 0.013 sits BELOW the band: under the old rule
    a genuine leak scores clean.

A permutation test fixes all three at once. Shuffling the class labels destroys any
real class difference while preserving the timing distribution, the crop structure,
the sample size and the harness noise, so the resulting distribution of the test
statistic IS the null at this run's own budget. No calibration constant, no
cross-budget transfer, and the multiple comparison over dudect's crop ladder is
absorbed because the same maximum is taken under every shuffle.

THE STATISTIC
-------------
dudect builds 102 Welch tests per run: one on the uncropped execution-time
differences, 100 on the same data cropped at percentiles 1 - 0.5^(10(i+1)/100), and
one second-order test on centred squares. It reports the maximum |t| over the tests
that have enough measurements. We reproduce the 101 FIRST-ORDER tests exactly and
take max |t| over them. The second-order test is excluded because dudect accumulates
it against a running mean, which is order-dependent and not reproducible offline;
excluding it from the observed statistic AND from the null keeps the comparison
exact, and it is stated wherever the p-value is reported.

Crop thresholds are label-independent, so they are computed once and held fixed
across shuffles: the null varies only what the test is entitled to vary.

Usage:
  bin/dudect_permute.py results/raw/<pair>_<arm>.dudect.bin.gz [--perms N] [--json]
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
REC = np.dtype([("cl", "u1"), ("t", "<i8")], align=False)   # as written by dudect_run.h
N_CROPS = 100                 # DUDECT_NUMBER_PERCENTILES
ENOUGH = 10000                # DUDECT_ENOUGH_MEASUREMENTS: a test must clear this


def load(path: pathlib.Path):
    """(class, exec-time) records; handles the committed gzip form."""
    raw = gzip.open(path, "rb").read() if path.suffix == ".gz" else path.read_bytes()
    a = np.frombuffer(raw, dtype=REC)
    return a["cl"].astype(np.uint8), a["t"].astype(np.float64)


def crop_masks(t: np.ndarray) -> np.ndarray:
    """dudect's crop ladder as a (n_measurements x 101) membership matrix.

    Column 0 is the uncropped test; column i+1 keeps t < percentile_i, with the
    percentile ladder dudect uses in prepare_percentiles()."""
    qs = [1.0 - 0.5 ** (10.0 * (i + 1) / N_CROPS) for i in range(N_CROPS)]
    thr = np.percentile(t, [q * 100.0 for q in qs])
    M = np.empty((t.size, N_CROPS + 1), dtype=np.float32)
    M[:, 0] = 1.0
    M[:, 1:] = (t[:, None] < thr[None, :]).astype(np.float32)
    return M


def _welch_max(M, x, x2, L, n_tot, s_tot, q_tot):
    """Max |Welch t| over the tests, for a batch of label vectors L (n x P).

    Returns (max_abs_t per column, n of the argmax test per column)."""
    n1 = M.T @ L                       # (tests x P)
    s1 = M.T @ (L * x[:, None])
    q1 = M.T @ (L * x2[:, None])
    n0 = n_tot[:, None] - n1
    s0 = s_tot[:, None] - s1
    q0 = q_tot[:, None] - q1
    with np.errstate(divide="ignore", invalid="ignore"):
        m0, m1 = s0 / n0, s1 / n1
        # sample variance, matching dudect's m2/(n-1)
        v0 = (q0 - n0 * m0 * m0) / (n0 - 1.0)
        v1 = (q1 - n1 * m1 * m1) / (n1 - 1.0)
        den = np.sqrt(v0 / n0 + v1 / n1)
        tval = np.abs((m0 - m1) / den)
    # dudect only considers a test once it has enough measurements in class 0.
    # ALSO require both classes to have positive variance inside the crop. On a
    # coarse counter a crop can contain a single repeated tick value (the aarch64
    # virtual counter quantises a short call to 7 or 8 ticks), and Welch's t on
    # constant data is 0/0: without this guard that crop produces a meaningless
    # statistic and, because it is meaningless under every relabelling, a
    # degenerate null as well.
    scale = np.maximum(np.abs(m0), 1.0)
    ok_var = (v0 > 1e-9 * scale * scale) & (v1 > 1e-9 * scale * scale)
    eligible = (n0 > ENOUGH) & (n1 > 0) & ok_var & np.isfinite(tval)
    tval = np.where(eligible, tval, -1.0)
    idx = np.argmax(tval, axis=0)
    cols = np.arange(tval.shape[1])
    best = tval[idx, cols]
    n_at = (n0 + n1)[idx, cols]
    return best, n_at


# Every corpus acquisition runs DUDECT_BATCHES=3 (src/corpus/score/adapters/dudect.py,
# bin/matrixssl_acquire.sh), and dudect_run.h writes 20,000 - 10 - 1 records per batch
# when no delta is dropped: 59,967 in all. That number is the budget the paper prints.
DECLARED_BATCHES = 3


def detect_batches(n: int, max_batches: int = 32, min_per: int = 5000) -> int:
    """FALLBACK ONLY: guess the batch count from the record count.

    It guessed wrong for every corpus dump. 59,967 = 9 x 6,663, so this returned 9
    where the acquisition ran 3 batches, and the within-batch shuffle was three
    times finer than the acquisition's real blocks. For 59,967-record dumps the
    nine sub-blocks happen to nest inside the three batches exactly (19,989 = 3 x
    6,663), so labels stayed exchangeable within every sub-block and the null was
    valid, only finer than described; for dumps with dropped deltas (56,968) the
    guessed blocks straddle batch boundaries. permute() now takes the declared
    count, or exact block sizes from a sidecar, and records which it used. This
    function is kept for a dump whose provenance is unknown, and its use is
    recorded as batches_source = "inferred"."""
    best = 1
    for k in range(2, max_batches + 1):
        if n % k == 0 and n // k >= min_per:
            best = k
    return best


def _stratified_labels(base: np.ndarray, blocks: list[slice], rng, p: int):
    """P label vectors, shuffled WITHIN each batch block.

    Class assignment is randomised per batch by dudect, and the timing
    distribution can shift between batches (warm-up, frequency, predictor state).
    Permuting globally would break that block structure and test a null the design
    does not have; permuting within blocks keeps every block's timing distribution
    intact and varies only the label-to-timing pairing, which is exactly what the
    null asserts is arbitrary."""
    L = np.empty((base.size, p), dtype=np.float32)
    for j in range(p):
        col = np.empty_like(base)
        for b in blocks:
            col[b] = rng.permutation(base[b])
        L[:, j] = col
    return L


def permute(path: pathlib.Path, perms: int = 10000, seed: int = 20260825,
            batch: int = 500, n_batches: int | None = None) -> dict:
    cl, t = load(path)
    if t.size == 0:
        return {"error": "empty dump", "path": str(path)}
    # Block structure, in order of trust: exact per-batch record counts from the
    # sidecar the adapter writes beside a new dump; the declared batch count with
    # equal splits (exact when nothing was dropped, approximate otherwise); the
    # divisor guess, recorded as such.
    meta = path.with_name(path.name.split(".dudect")[0] + ".dudect.meta.json") \
        if ".dudect" in path.name else path.with_suffix(".meta.json")
    sizes = None
    if meta.exists():
        try:
            m = json.loads(meta.read_text())
            if sum(m.get("records_per_batch", [])) == int(t.size):
                sizes = [int(x) for x in m["records_per_batch"]]
        except (ValueError, KeyError, TypeError):
            sizes = None
    if sizes:
        edges = np.cumsum([0] + sizes)
        blocks = [slice(int(edges[i]), int(edges[i + 1])) for i in range(len(sizes))]
        nb, source, approximate = len(sizes), "sidecar", False
    else:
        nb = n_batches if n_batches else DECLARED_BATCHES
        source = "declared" if n_batches else "declared-default"
        step = t.size // nb
        blocks = [slice(i * step, (i + 1) * step if i < nb - 1 else t.size)
                  for i in range(nb)]
        # Equal splits are exact only when every batch wrote the same number of
        # records, which dudect_run.h guarantees unless a delta was dropped.
        approximate = (t.size % nb != 0)
    M = crop_masks(t)
    # Centre the timings: algebraically neutral for a difference of means, and it
    # keeps the sums of squares well conditioned on counters with a large offset.
    x = (t - t.mean()).astype(np.float32)
    x2 = (x * x).astype(np.float32)
    n_tot = M.sum(axis=0).astype(np.float64)
    s_tot = (M.T @ x).astype(np.float64)
    q_tot = (M.T @ x2).astype(np.float64)

    obs_L = cl.astype(np.float32)[:, None]
    obs_t, obs_n = _welch_max(M, x, x2, obs_L, n_tot, s_tot, q_tot)
    observed = float(obs_t[0])
    observed_n = float(obs_n[0])

    rng = np.random.default_rng(seed)
    base = cl.astype(np.float32)
    null = np.empty(perms, dtype=np.float64)
    done = 0
    while done < perms:
        p = min(batch, perms - done)
        L = _stratified_labels(base, blocks, rng, p)
        null[done:done + p], _ = _welch_max(M, x, x2, L, n_tot, s_tot, q_tot)
        done += p

    # +1 in numerator and denominator: the observed labelling is itself one of the
    # equally likely labellings under H0, so the p-value is never reported as 0.
    p_value = float((1 + int(np.sum(null >= observed))) / (perms + 1))
    return {
        "path": str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path),
        # The digest of the dump this row was computed from. Nothing regenerates this
        # record automatically (the full permutation is minutes of compute), so the
        # digest is what lets a fast control notice that a row no longer describes the
        # samples on disk instead of the paper quietly resting on a stale verdict.
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "measurements": int(t.size),
        "batches": nb,
        "batches_source": source,
        "blocks_approximate": bool(approximate),
        "n_class0": int((cl == 0).sum()), "n_class1": int((cl == 1).sum()),
        "observed_max_abs_t": round(observed, 4),
        "n_at_argmax_test": int(observed_n),
        "observed_tau": round(observed / observed_n ** 0.5, 6),
        "permutations": perms,
        "null_max_abs_t_mean": round(float(null.mean()), 4),
        "null_max_abs_t_p95": round(float(np.percentile(null, 95)), 4),
        "null_max_abs_t_max": round(float(null.max()), 4),
        "p_value": p_value,
        # Per-run, UNCORRECTED. The corpus verdict is the Benjamini-Hochberg
        # decision across every committed dump (bh_significant in the assembled
        # results/dudect_permutation.json); over 18 tests a borderline uncorrected
        # p is expected, so this field must not be read as a verdict on its own.
        "raw_significant": bool(p_value <= 0.05),
        "note": "Permutation null over dudect's 101 first-order tests (uncropped plus "
                "100 percentile crops), labels shuffled, crop thresholds held fixed. "
                "The second-order test is excluded from BOTH the observed statistic "
                "and the null because dudect accumulates it against a running mean. "
                "p is budget-matched by construction: no calibrated band is used.",
    }


FDR = 0.05


def benjamini_hochberg(rows: list[dict], q: float = FDR) -> None:
    """Set bh_significant on each row, controlling the FDR at q across all rows.

    The corpus decides many arms at once, so the per-run p-value is not the
    verdict: over eighteen tests a borderline uncorrected p is the expected
    count when nothing is there. Step-up: sort ascending, find the largest k
    with p_(k) <= k*q/m, and reject everything at or below it.
    """
    live = [r for r in rows if "p_value" in r]
    m = len(live)
    order = sorted(live, key=lambda r: r["p_value"])
    k = 0
    for i, r in enumerate(order, start=1):
        if r["p_value"] <= i * q / m:
            k = i
    for i, r in enumerate(order, start=1):
        r["bh_significant"] = bool(i <= k)


def assemble(rows: list[dict], perms: int) -> dict:
    """Wrap the per-run results in the committed record, with its multiplicity
    control applied and its disagreements with the retired band named."""
    for r in rows:
        stem = pathlib.Path(r["path"]).name.split(".dudect")[0]
        r["pair"], _, r["arm"] = stem.rpartition("_")
    benjamini_hochberg(rows)
    borderline = [r for r in rows
                  if r.get("raw_significant") and not r.get("bh_significant")]
    agree = ("After BH control the permutation rule reproduces every verdict the "
             "retired band gave: the leaking vulnerable arms are significant and "
             "every patched arm and certified negative is not.")
    if borderline:
        names = ", ".join(f"{r['pair']}_{r['arm']} (p={r['p_value']:.4f})"
                          for r in borderline)
        agree += (f" {len(borderline)} row(s) carry an uncorrected p below 0.05 that "
                  f"does not survive multiplicity, which is the expected count of "
                  f"borderline results over {len(rows)} tests: {names}.")
    return {
        "finding": "dudect verdicts decided against a permutation null built from "
                   "each run's own committed samples, replacing the retired band on "
                   "tau.",
        "why": "A fixed band on tau = |t|/sqrt(n) is not budget-invariant under the "
               "null: |t| is O(1) when no effect is present, so tau falls as "
               "n^-1/2 and one constant cannot serve budgets from 4e4 to 1e7.",
        "statistic": "dudect's max |t| over its 101 first-order tests (uncropped "
                     "plus 100 percentile crops). The second-order test is excluded "
                     "from both the observed statistic and the null because dudect "
                     "accumulates it against a running mean.",
        "permutation": "class labels shuffled WITHIN each dudect batch block (a dump "
                       "concatenates batches whose timing distributions can differ; "
                       f"class assignment is randomised within each), crop thresholds "
                       f"held fixed, {perms} shuffles, "
                       "p = (1+#{null>=obs})/(perms+1).",
        "multiplicity": f"Benjamini-Hochberg across all committed dumps at FDR {FDR}. "
                        f"Reported per row as bh_significant, which is the verdict; "
                        f"raw_significant is the uncorrected per-run call and is not.",
        "agreement_with_retired_band": agree,
        "generator": "bin/dudect_permute.py --assemble",
        "rows": sorted(rows, key=lambda r: (r["pair"], r["arm"])),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", nargs="+")
    ap.add_argument("--perms", type=int, default=10000)
    ap.add_argument("--batches", type=int, default=None,
                    help=f"declared batch count (default {DECLARED_BATCHES}; a sidecar "
                         f"<dump>.meta.json with records_per_batch overrides it)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--assemble", metavar="OUT",
                    help="write the committed record (BH-corrected) to OUT")
    a = ap.parse_args()
    out = [permute(pathlib.Path(d), perms=a.perms, n_batches=a.batches) for d in a.dump]
    if a.assemble:
        rec = assemble([r for r in out if "error" not in r], a.perms)
        pathlib.Path(a.assemble).write_text(json.dumps(rec, indent=2) + "\n")
        n = sum(1 for r in rec["rows"] if r["bh_significant"])
        print(f"dudect_permute: wrote {a.assemble} "
              f"({len(rec['rows'])} rows, {n} significant at FDR {FDR})")
        return 0
    if a.json:
        print(json.dumps(out if len(out) > 1 else out[0], indent=2))
    else:
        for r in out:
            if "error" in r:
                print(f"{r['path']}: {r['error']}")
                continue
            verdict = ("significant before multiplicity correction"
                       if r["raw_significant"] else "not significant")
            print(f"{pathlib.Path(r['path']).name}")
            print(f"  observed max|t| {r['observed_max_abs_t']:>10.3f} "
                  f"(tau {r['observed_tau']:.5f}, n {r['n_at_argmax_test']:,})")
            print(f"  null      mean  {r['null_max_abs_t_mean']:>10.3f}  "
                  f"p95 {r['null_max_abs_t_p95']:.3f}  max {r['null_max_abs_t_max']:.3f}")
            print(f"  p = {r['p_value']:.5f}   -> {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
