#!/usr/bin/env python3
"""A signature-budget bound for an error-tolerant attack on the MatrixSSL residual.

WHY THIS EXISTS
The nine timing-ordered lattice attempts on the fixed build recover nothing, and
the instrument they use tolerates no misclassification. A reviewer asked what an
error-tolerant attack would need, so that the site-closure outcome incomplete
carries a security consequence rather than a bare measurement. This script runs
no attack. It bounds the budget such an attack would need from the measured
per-bit signal and noise, and prints the bound as an estimate beside the
assumptions it rests on.

WHAT IT COMPUTES
From the committed one-bit dump of the first fixed release, under the same
95th-percentile crop the site estimator uses: the class difference, which is the
per-bit signal; the pooled standard deviation, which is the per-measurement
noise; their ratio, the signal-to-noise ratio; and the minimum detectable effect
the paper prints, as a cross-check. From the committed exploit-budget records:
how pure the timing order is at its top ranks, and how small a fraction of a
trace those ranks are. Then the Bleichenbacher accounting. A single-shot
threshold oracle at that ratio errs with probability Phi of minus half the
ratio. Its bias is one minus twice that error, times two over pi, the bias of a
perfect one-bit oracle. Each round of sum reduction squares the bias, so r
rounds take it to the power two to the r. The samples the attack needs scale as
a constant over the bias squared, and the constant is carried explicitly. The
usable fraction converts samples into raw signatures, because the purity holds
only over the top ranks of a trace.

THE READING
The bound is an estimate, not a measurement, and it is astronomically past the
budgets tried: at one round of reduction the attack needs about half a million
signatures, at the two rounds a 256-bit group realistically needs about three
hundred billion, and delivering the usable samples the published Fourier attack
needed on a smaller group would take about six hundred billion raw signatures,
because the purity the order supplies holds over the fastest ninety of a
hundred thousand. So the residual is incomplete with a quantified bound, and it
does not move to attenuated: Definition 5 decides residual exploitability by a
recovery, and a bound is not one.

ASSUMPTIONS
the two classes are Gaussian with equal variance, so a midpoint threshold errs with probability Phi(-SNR/2)
the oracle is single-shot: one signature, one guess, no repeated measurement of the same nonce
a perfect one-bit oracle has bias 2/pi, and a noisy one scales it by one minus twice its error
each Bleichenbacher sum-reduction round squares the bias, and a 256-bit group needs at least two
the samples needed scale as c over the bias squared, with c = 1 and the FFT's time and memory ignored
the usable fraction is the top ninety of a hundred thousand, where the measured purity holds
the noise is this host's under the site design, and the bound is host-conditional like every timing figure here
this is a feasibility bound under the published attack's information model, not a demonstrated recovery

Usage: matrixssl_budget_bound.py [--write] [--check]
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "matrixssl_budget_bound.json"
DUMP = REPO / "results" / "raw" / "matrixssl" / "repeats" / "4-3-0.bit255.r1.bin.gz"
BUDGETS = (50000, 100000)
RECOVERY = REPO / "results" / "matrixssl_recovery.json"
CROP_PCT = 95.0          # the crop bin/matrixssl_report.py uses for the site figures
ALPHA, POWER = 0.05, 0.8  # the paper's MDE convention
C_CONSTANT = 1.0          # Bleichenbacher: samples ~ c / bias^2, c carried explicitly
ROUNDS = (1, 2, 3)
USABLE_TOP = 90           # the rank depth at which the purity is measured
# The published Fourier attack's anchor, verbatim from its paper: it reached a 192-bit
# group with 2^29 to 2^43 signatures and an oracle cleaner than this one.
LADDERLEAK = {"group_bits": 192, "signatures_log2_low": 29, "signatures_log2_high": 43,
              "cite": "ladderleak"}


def _load_dump(path: pathlib.Path):
    """The committed dump through bin/dudect_ci.py's guarded loader."""
    spec = importlib.util.spec_from_file_location("dudect_ci", REPO / "bin" / "dudect_ci.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cl, t = mod.load(path)
    return np.asarray(cl).astype(np.int64), np.asarray(t).astype(np.float64)


def measured(cl: np.ndarray, t: np.ndarray, crop_pct: float = CROP_PCT) -> dict:
    """Signal, noise and their ratio under the site estimator's crop."""
    keep = t <= np.percentile(t, crop_pct)
    cl, t = cl[keep], t[keep]
    t0, t1 = t[cl == 0], t[cl == 1]
    s0, s1 = t0.std(ddof=1), t1.std(ddof=1)
    pooled = math.sqrt(((t0.size - 1) * s0 ** 2 + (t1.size - 1) * s1 ** 2) / (t0.size + t1.size - 2))
    delta = float(t1.mean() - t0.mean())
    se = math.sqrt(s0 ** 2 / t0.size + s1 ** 2 / t1.size)
    z = NormalDist().inv_cdf(1 - ALPHA / 2) + NormalDist().inv_cdf(POWER)
    return {"cropped_sample_size": int(t.size), "n_class0": int(t0.size), "n_class1": int(t1.size),
            "signal_ticks": delta, "noise_sd_ticks": pooled, "snr": delta / pooled,
            "se_ticks": se, "mde_ticks": z * se}


def bound(snr: float, usable_fraction: float, c: float = C_CONSTANT) -> dict:
    """The Bleichenbacher accounting from a signal-to-noise ratio."""
    eps = NormalDist().cdf(-snr / 2)
    b0 = (1 - 2 * eps) * (2 / math.pi)
    rounds = {}
    for r in ROUNDS:
        b = b0 ** (2 ** r)
        rounds[str(r)] = {"bias": b, "signatures": c / b ** 2}
    target = 2 ** LADDERLEAK["signatures_log2_low"]
    return {"oracle_error": eps, "bias_single_shot": b0, "constant_c": c, "rounds": rounds,
            "usable_fraction": usable_fraction,
            "raw_signatures_for_ladderleak_low": target / usable_fraction}


def build() -> dict:
    cl, t = _load_dump(DUMP)
    m = measured(cl, t)
    purity = {}
    for n in BUDGETS:
        f = REPO / "results" / f"exploit_budget_matrixssl_{n}.json"
        if f.exists():
            e = json.loads(f.read_text())
            sq = e.get("selection_quality", {})
            purity[str(n)] = {"auc": e.get("auc_time_vs_short_nonce"),
                              **{k: sq[k] for k in ("top_90", "top_200", "top_500") if k in sq}}
    frac = USABLE_TOP / max(BUDGETS)
    rec = json.loads(RECOVERY.read_text()) if RECOVERY.exists() else {}
    doc_ = __doc__
    return {
        "finding": ("an error-tolerant attack on the MatrixSSL residual is bounded, from the "
                    "measured per-bit signal and noise, at budgets astronomically past the "
                    "ones tried; the site outcome stays incomplete with a quantified bound"),
        "why": doc_.split("WHY THIS EXISTS")[1].split("WHAT IT COMPUTES")[0].strip(),
        "method": doc_.split("WHAT IT COMPUTES")[1].split("THE READING")[0].strip(),
        "reading": doc_.split("THE READING")[1].split("ASSUMPTIONS")[0].strip(),
        "assumptions": [ln.strip() for ln in doc_.split("ASSUMPTIONS")[1].split("Usage:")[0].splitlines()
                        if ln.strip()],
        "label": "estimate",
        "generator": "bin/matrixssl_budget_bound.py --write",
        "dump": str(DUMP.relative_to(REPO)),
        "crop_pct": CROP_PCT,
        "measured": m,
        "purity_by_rank": purity,
        "bound": bound(m["snr"], frac),
        "ladderleak_anchor": LADDERLEAK,
        "key_bits": rec.get("key_bits", 256),
        "lattice_attempts": rec.get("attempts_total"),
    }


def _sci(x: float) -> str:
    e = int(math.floor(math.log10(x)))
    return f"{x / 10 ** e:.0f}\\times10^{{{e}}}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    if a.check:
        if not OUT.exists():
            print("matrixssl_budget_bound: no committed record", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text())
        bad = []
        for k in ("cropped_sample_size", "signal_ticks", "noise_sd_ticks", "snr", "mde_ticks"):
            o, n = old.get("measured", {}).get(k), doc["measured"][k]
            if o is None or abs(float(o) - float(n)) > 1e-6 * max(1.0, abs(float(n))):
                bad.append(f"measured.{k}")
        for r in ROUNDS:
            o = old.get("bound", {}).get("rounds", {}).get(str(r), {}).get("signatures")
            n = doc["bound"]["rounds"][str(r)]["signatures"]
            if o is None or abs(float(o) - n) > 1e-6 * n:
                bad.append(f"bound.rounds.{r}")
        if bad:
            print("matrixssl_budget_bound: differs from committed: " + ", ".join(bad), file=sys.stderr)
            return 1
        print(f"matrixssl_budget_bound: check clean (SNR {doc['measured']['snr']:.3f}, "
              f"{len(ROUNDS)} rounds)")
        return 0
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"matrixssl_budget_bound: wrote {OUT.relative_to(REPO)}")
    m, b = doc["measured"], doc["bound"]
    print(f"  signal {m['signal_ticks']:.1f} ticks, sd {m['noise_sd_ticks']:.0f}, SNR {m['snr']:.3f}, "
          f"MDE {m['mde_ticks']:.1f}")
    print(f"  oracle error {b['oracle_error']:.3f}, bias {b['bias_single_shot']:.4f}")
    for r in ROUNDS:
        print(f"  {r} round(s): {b['rounds'][str(r)]['signatures']:.2e} signatures")
    print(f"  raw for 2^{LADDERLEAK['signatures_log2_low']} usable: {b['raw_signatures_for_ladderleak_low']:.2e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
