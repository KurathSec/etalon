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
import re
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
    ap.add_argument("--backfill", action="store_true",
                    help="recover the verdict statistic for rows acquired before it was "
                         "a field, from the committed detail string those same runs wrote, "
                         "and re-run nothing. Fails closed if any scored row cannot be "
                         "parsed, because a partly filled column is worse than an empty one.")
    a = ap.parse_args()

    if a.backfill:
        path = REPO / a.out
        doc = json.loads(path.read_text())
        filled, bad = 0, []
        for r in doc["rows"]:
            if not r.get("status"):
                continue
            if "dudect_max_t" not in r and "max_abs_t" in r:
                r["dudect_max_t"] = r.pop("max_abs_t")
            if r.get("permutation_max_abs_t") is not None:
                continue
            m = re.search(r"max \|t\|=([0-9.]+) against this run's own permutation null",
                          str(r.get("detail", "")))
            if not m:
                bad.append(f"{r['pair']}/{r['arm']} amp={r['amp']}")
                continue
            r["permutation_max_abs_t"] = float(m.group(1))
            filled += 1
        if bad:
            print("backfill refused, no verdict statistic recoverable for: "
                  + ", ".join(bad), file=sys.stderr)
            return 1
        path.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"backfill: {filled} row(s) gained permutation_max_abs_t, nothing re-run")
        return 0

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
                    # Two statistics, named apart. `dudect_max_t` is the tool's own
                    # maximum over every test it runs; `permutation_max_abs_t` is the
                    # one the verdict rule of PR-4 is defined on, which excludes the
                    # second-order test. The field was called `max_abs_t` and held the
                    # first while every reader took it for the second.
                    "dudect_max_t": r.get("max_t"),
                    "permutation_max_abs_t": r.get("permutation_max_abs_t"),
                    "permutation_p": r.get("permutation_p"),
                    "detail": str(r.get("detail"))[:200],
                })
                print(f"{pair}/{arm} amp={amp}: {r.get('status')} "
                      f"|t|={r.get('max_t')} p={r.get('permutation_p')}", flush=True)

    scored = [r for r in rows if r.get("status") and r["arm"] == "vulnerable"]
    detects_at_one = sorted({r["pair"] for r in scored
                             if r["amp"] == 1 and r["status"] == "leak_reported"})
    # A DETECTION is both arms: a leak on the vulnerable one and none on the patched.
    # The list above is the vulnerable half only, and the paper had come to describe it
    # as discrimination, which is the stronger claim. Compute the stronger claim rather
    # than let the prose and the emitter drift; on this corpus the two sets coincide,
    # and that coincidence is now a fact the file records instead of an assumption the
    # prose makes.
    _patched_at_one = {r["pair"]: r["status"] for r in rows
                       if r.get("status") and r["arm"] == "patched" and r["amp"] == 1}
    discriminates_at_one = sorted(p for p in detects_at_one
                                  if _patched_at_one.get(p) == "clean")
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
        "pairs_discriminating_at_factor_one": discriminates_at_one,
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
