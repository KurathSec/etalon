#!/usr/bin/env python3
"""Summarise the MatrixSSL acquisitions, across repeats, from raw dumps.

The point of the repeats is the one thing the earlier acquisition could not give:
a between-acquisition spread. Every interval the paper reported on this case came
from a single run, so it bounded sampling within that run and nothing bounded the
variation between runs. With repeats the spread is measured, and the effect is
reported as a mean over acquisitions with the observed range beside it.

Dumps are the driver's raw format: one byte of class, then a little-endian int64
of ticks, per measurement.
"""
import argparse
import gzip
import json
import pathlib
import re
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent

NAME = re.compile(r"^(?P<ver>[0-9-]+)\.(?P<design>[a-z0-9]+)\.r(?P<rep>\d+)\.bin(?:\.gz)?$")


def load(path):
    raw = gzip.open(path, "rb").read() if str(path).endswith(".gz") else path.read_bytes()
    n = len(raw) // 9
    if n == 0:
        return None, None
    a = np.frombuffer(raw[: n * 9], dtype=np.uint8).reshape(n, 9)
    cl = a[:, 0].astype(np.int64)
    t = a[:, 1:].copy().view(np.int64).ravel()
    # The same guard bin/dudect_ci.py uses: a class outside {0,1} or an absurd tick
    # count means the file is not what it is supposed to be, and a silent misparse
    # of a container as records is a failure this project has already had once.
    keep = (cl < 2) & (t > 0) & (t < 2**40)
    if keep.sum() < n // 2:
        sys.exit(f"{path.name}: only {keep.sum()} of {n} records are plausible")
    return cl[keep], t[keep]


# The same crop the headline estimator uses. Two estimators that disagree would let
# the between-acquisition spread be reported against a number no other part of the
# paper prints, which is how a summary comes to contradict what it summarises.
CROP_PCT = 95.0


def stats(cl, t, boot=2000, seed=0):
    """Class difference in ticks with a bootstrap 95% interval, on the same crop."""
    keep = t <= np.percentile(t, CROP_PCT)
    cl, t = cl[keep], t[keep]
    a, b = t[cl == 0], t[cl == 1]
    d = float(b.mean() - a.mean())
    rng = np.random.default_rng(seed)
    bs = np.empty(boot)
    for i in range(boot):
        bs[i] = (rng.choice(b, b.size, replace=True).mean()
                 - rng.choice(a, a.size, replace=True).mean())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return d, float(lo), float(hi), int(t.size)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dumps")
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--check", action="store_true",
                    help="re-derive every design from the dumps and compare with the "
                         "committed results/matrixssl_repeats.json; exit 1 on any "
                         "difference. The bootstrap is seeded, so this is exact.")
    a = ap.parse_args()

    rows = {}
    for p in sorted(pathlib.Path(a.dumps).glob("*.bin*")):
        m = NAME.match(p.name)
        if not m:
            continue
        cl, t = load(p)
        if cl is None:
            print(f"  {p.name}: empty, skipped", file=sys.stderr)
            continue
        d, lo, hi, n = stats(cl, t)
        rows.setdefault((m["ver"], m["design"]), []).append(
            {"rep": int(m["rep"]), "effect_ticks": d, "ci_low": lo, "ci_high": hi,
             "measurements": n})

    out = {}
    print(f"  {'version':8s} {'design':10s} {'reps':>4s} {'mean effect':>14s} "
          f"{'range over reps':>22s} {'each CI excludes 0':>20s}")
    for (ver, design), reps in sorted(rows.items()):
        e = [r["effect_ticks"] for r in reps]
        excl = sum(1 for r in reps if (r["ci_low"] > 0) == (r["ci_high"] > 0))
        out[f"{ver}.{design}"] = {
            "repeats": len(reps), "mean_effect_ticks": float(np.mean(e)),
            "min_effect_ticks": float(min(e)), "max_effect_ticks": float(max(e)),
            # The spread BETWEEN acquisitions, which is the quantity a single
            # acquisition cannot supply at any budget.
            "between_acquisition_range_ticks": float(max(e) - min(e)),
            "reps_with_interval_excluding_zero": excl,
            "per_rep": sorted(reps, key=lambda r: r["rep"]),
        }
        print(f"  {ver:8s} {design:10s} {len(reps):4d} {np.mean(e):14.1f} "
              f"{f'[{min(e):.1f}, {max(e):.1f}]':>22s} {f'{excl}/{len(reps)}':>20s}")

    doc = {"finding": "the MatrixSSL residual across repeated acquisitions",
           "why": ("Every interval previously reported on this case came from one "
                   "acquisition, so none bounded between-acquisition spread. These "
                   "repeat the same design on the same retained build."),
           "generator": ("bin/matrixssl_report.py results/raw/matrixssl/repeats "
                         "--json results/matrixssl_repeats.json"),
           "designs": out}

    if a.check:
        # The dumps are committed (results/raw/matrixssl/repeats, three per design)
        # and the bootstrap is seeded, so the record must reproduce exactly. Every
        # numeric field of every design and every repetition is compared; GEN-2 runs
        # this so the printed means and ranges cannot drift from the samples.
        committed = json.loads((REPO / "results" / "matrixssl_repeats.json").read_text())
        bad = []
        for k, v in committed["designs"].items():
            w = doc["designs"].get(k)
            if w is None:
                bad.append(f"{k}: no dumps")
                continue
            for f in ("repeats", "mean_effect_ticks", "min_effect_ticks",
                      "max_effect_ticks", "between_acquisition_range_ticks",
                      "reps_with_interval_excluding_zero"):
                if abs(float(v[f]) - float(w[f])) > 1e-6:
                    bad.append(f"{k}.{f}: {v[f]} != {w[f]}")
            for r1, r2 in zip(v["per_rep"], w["per_rep"]):
                for f in ("effect_ticks", "ci_low", "ci_high", "measurements"):
                    if abs(float(r1[f]) - float(r2[f])) > 1e-6:
                        bad.append(f"{k}.r{r1['rep']}.{f}: {r1[f]} != {r2[f]}")
        extra = set(doc["designs"]) - set(committed["designs"])
        if extra:
            bad.append("dumps for designs the record does not carry: " + ", ".join(sorted(extra)))
        if bad:
            print("matrixssl_report: " + "; ".join(bad[:6]), file=sys.stderr)
            return 1
        print(f"matrixssl_report: check clean ({len(committed['designs'])} designs, "
              f"{sum(len(v['per_rep']) for v in committed['designs'].values())} acquisitions)")
        return 0

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(doc, indent=1) + "\n")
        print(f"\n  wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
