#!/usr/bin/env python3
"""The five-pair detection curve PR-2 registered, run at last.

WHY THIS EXISTS
---------------
PR-2 registered a detection curve over amplification factors {1, 2, 4, 8} for five
pairs. What shipped was narrower: one pair, and one scalar per factor. PR-3 recorded
that as a deviation and committed to running the registered version; PR-4 recorded
that the commitment was still undischarged. The blocker was that each pair's
amplification was compiled in rather than exposed, so sweeping it meant rebuilding.
Each pair now guards its constant with `#ifndef AMP`, so the sweep is a build-time
parameter and the default build is unchanged.

WHAT IT REPORTS
---------------
Per pair and factor, on the vulnerable arm: dudect's max |t|, the permutation
p-value against that run's own samples, and whether the run rejects. The question
the curve answers is not "is there a leak" but "does amplification surface one":
a leak already detectable at factor 1 needs no gain, and a statistic that does not
grow with gain is not a sub-noise signal waiting for more of it.

The patched arm is swept too, because a curve on the vulnerable arm alone cannot
distinguish a signal that grows from a measurement artifact that grows.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
FACTORS = [1, 2, 4, 8]
# The five pairs PR-2 named. libgcrypt-minerva and the observation datasets have no
# buildable two-class harness, so they were never in the registered set.
PAIRS = ["ecdsa-nonce", "ecdsa-address", "kyberslash", "hqc-reject", "hmac-timing"]


def _adapter():
    spec = importlib.util.spec_from_file_location(
        "dudect", REPO / "src" / "corpus" / "score" / "adapters" / "dudect.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=",".join(PAIRS))
    ap.add_argument("--factors", default=",".join(str(f) for f in FACTORS))
    ap.add_argument("--out", default="results/detection_curve_all.json")
    a = ap.parse_args()
    dud = _adapter()
    pairs = [p for p in a.pairs.split(",") if p]
    factors = [int(f) for f in a.factors.split(",")]

    rows = []
    for pair in pairs:
        pd = REPO / "pairs" / pair
        if not (pd / "harness" / "dudect.toml").exists():
            rows.append({"pair": pair, "skipped": "no dudect harness"})
            print(f"{pair}: no dudect harness, skipped", flush=True)
            continue
        for amp in factors:
            for arm in ("vulnerable", "patched"):
                r = dud.score(pd, arm, amp=amp, save_raw=False)
                rows.append({
                    "pair": pair, "arm": arm, "amp": amp,
                    "status": r.get("status"),
                    "max_abs_t": r.get("max_t"),
                    "permutation_p": r.get("permutation_p"),
                    "detail": str(r.get("detail"))[:200],
                })
                print(f"{pair}/{arm} amp={amp}: {r.get('status')} "
                      f"|t|={r.get('max_t')} p={r.get('permutation_p')}", flush=True)

    scored = [r for r in rows if r.get("status") and r["arm"] == "vulnerable"]
    detects_at_one = sorted({r["pair"] for r in scored
                             if r["amp"] == 1 and r["status"] == "leak_reported"})
    doc = {
        "finding": "the five-pair detection curve registered in PR-2",
        "why": __doc__.split("WHY THIS EXISTS")[1].split("WHAT IT REPORTS")[0].strip(),
        "reading": ("A pair that already rejects at factor 1 gains nothing from "
                    "amplification and its curve is uninformative about whether gain "
                    "surfaces a leak. A pair whose statistic does not grow with the "
                    "factor is not carrying a sub-noise signal that more gain would "
                    "reveal. Both readings are about the SHAPE; no single point here "
                    "is a verdict on a pair, which is what results/verdicts.jsonl "
                    "carries at the committed full budget."),
        "factors": factors,
        "pairs_detecting_at_factor_one": detects_at_one,
        "rows": rows,
        "generator": "bin/detection_curve_all.py",
        "discharges": ("the PR-2 commitment recorded as outstanding in PR-3 and again "
                       "in PR-4"),
    }
    (REPO / a.out).write_text(json.dumps(doc, indent=2) + "\n")
    print(f"\nwrote {a.out}: {len(rows)} rows")
    print("pairs already detecting at factor 1:", detects_at_one or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
