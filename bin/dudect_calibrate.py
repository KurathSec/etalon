#!/usr/bin/env python3
"""Calibrate dudect's clean threshold on the constant-time negative sentinel.

The negative sentinel is a constant-time comparison: any tau it produces is null,
the effect of measurement noise on a program with no leak. Running it many times
at the scoring budget gives the null distribution of tau; the clean threshold is
its upper edge with a margin, so a real arm counts as a leak only when its tau
exceeds what a genuinely constant-time program produces on this host. Replaces the
arbitrary |t| in {10, 500} band with an empirically justified number, per PR-3.

Writes results/dudect_calibration.json.
"""
from __future__ import annotations

import importlib.util
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "dudect_calibration.json"

_spec = importlib.util.spec_from_file_location(
    "dudect_adapter", REPO / "src" / "corpus" / "score" / "adapters" / "dudect.py")
_ad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ad)


def main() -> int:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    pair = REPO / "pairs" / "_sentinel-negative"
    taus, ts = [], []
    for i in range(runs):
        r = _ad.score(pair, "vulnerable", save_raw=False)
        if r.get("max_tau") is not None:
            taus.append(r["max_tau"])
            ts.append(abs(r["max_t"]))
            print(f"run {i+1}/{runs}: tau={r['max_tau']:.3g} |t|={abs(r['max_t']):.1f}",
                  flush=True)
    if not taus:
        print("no tau samples", file=sys.stderr)
        return 1
    taus.sort()
    hi = max(taus)
    margin = 1.3
    threshold = hi * margin
    doc = {
        "_meaning": "Null distribution of dudect's tau on the constant-time negative "
                    "sentinel at the scoring budget. null_threshold_tau is the largest "
                    "observed null tau times a safety margin; an arm counts as a leak only "
                    "above it. tau = t / sqrt(measurements), the budget-invariant effect "
                    "size, so this transfers across pairs run at the same budget. The "
                    "sentinel is a tag comparison, so the null it characterises is this "
                    "host's noise on constant-time code, not the specific noise of every "
                    "operation scored.",
        "budget": {"measurements_per_batch": _ad.MEASUREMENTS, "batches": _ad.BATCHES,
                   "total_measurements": _ad.MEASUREMENTS * _ad.BATCHES},
        "runs": len(taus),
        "null_tau_samples": taus,
        "null_tau_max": hi,
        "null_tau_median": statistics.median(taus),
        "null_t_max": max(ts),
        "margin": margin,
        "null_threshold_tau": threshold,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"\nnull tau: median {doc['null_tau_median']:.3g}, max {hi:.3g}; "
          f"threshold {threshold:.3g} (max x {margin})")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
