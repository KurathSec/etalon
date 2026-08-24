#!/usr/bin/env python3
"""Effect size and bootstrap confidence interval for a dudect raw sample dump.

The dump is a stream of records written by dudect_run.h: one uint8 class label
followed by one int64 execution time, per measurement. This computes the class
difference of means in ticks (the effect size an attacker actually consumes) and
a bootstrap 95% confidence interval for it, after cropping the pooled upper tail
to shed scheduler outliers the way dudect's own percentile step does.

The verdict itself is decided elsewhere (bin/score.py) against a null band
calibrated on the constant-time negative sentinel, so this file computes a
magnitude, never a pass/fail.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REC = np.dtype([("cl", "u1"), ("t", "<i8")], align=False)  # 9-byte records


def load(path: Path):
    a = np.fromfile(path, dtype=REC)
    return a["cl"], a["t"].astype(np.float64)


def analyse(cl: np.ndarray, t: np.ndarray, crop_pct: float = 95.0,
            boot: int = 2000, boot_n: int = 20000, seed: int = 12345) -> dict:
    """Effect size (mean class1 - mean class0, in ticks) and its bootstrap 95% CI."""
    if t.size == 0:
        return {"effect_ticks": None, "ci_low": None, "ci_high": None,
                "n0": 0, "n1": 0, "note": "empty dump"}
    keep = t <= np.percentile(t, crop_pct)      # shed the pooled upper tail
    cl, t = cl[keep], t[keep]
    t0, t1 = t[cl == 0], t[cl == 1]
    if t0.size == 0 or t1.size == 0:
        return {"effect_ticks": None, "ci_low": None, "ci_high": None,
                "n0": int(t0.size), "n1": int(t1.size), "note": "a class is empty"}
    effect = float(t1.mean() - t0.mean())
    rng = np.random.default_rng(seed)
    # Bootstrap the difference of means; subsample each class to boot_n per draw
    # so a large dump stays fast, which does not bias the mean estimate.
    m0 = min(t0.size, boot_n)
    m1 = min(t1.size, boot_n)
    diffs = np.empty(boot, dtype=np.float64)
    for b in range(boot):
        d0 = t0[rng.integers(0, t0.size, m0)].mean()
        d1 = t1[rng.integers(0, t1.size, m1)].mean()
        diffs[b] = d1 - d0
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"effect_ticks": effect, "ci_low": float(lo), "ci_high": float(hi),
            "n0": int(t0.size), "n1": int(t1.size),
            "ci_excludes_zero": bool(lo > 0 or hi < 0)}


def analyse_path(path: Path, **kw) -> dict:
    cl, t = load(path)
    return analyse(cl, t, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dump", type=Path)
    a = ap.parse_args()
    print(json.dumps(analyse_path(a.dump), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
