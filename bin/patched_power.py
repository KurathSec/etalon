#!/usr/bin/env python3
"""Effect size and bootstrap CI for every patched arm, so a clean verdict carries its power.

A clean verdict is the paper's most common result and the least informative one as printed:
"no leak reported" says nothing about what size of leak would have been reported. Blind
review asked for the missing half, and it is computable from dumps already committed, so
there is no reason for it to be missing.

For each patched arm this records the class difference of means in ticks with its bootstrap
95% CI. The CI half-width is the useful number: it bounds what an effect would have had to
exceed at this budget to be distinguishable from zero, which is a statement about the
measurement's power rather than about the program.

Usage: bin/patched_power.py [--out results/patched_power.json]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent


def _ci():
    spec = importlib.util.spec_from_file_location("dudect_ci", REPO / "bin" / "dudect_ci.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "results" / "patched_power.json"))
    a = ap.parse_args()
    C = _ci()

    arms = {}
    for dump in sorted((REPO / "results" / "raw").glob("*_patched.dudect.bin.gz")):
        pair = dump.name.split("_patched")[0]
        cl, t = C.load(dump)
        r = C.analyse(cl, t)
        if r["effect_ticks"] is None:
            continue
        half = (r["ci_high"] - r["ci_low"]) / 2.0
        arms[pair] = {
            "measurements": int(t.size),
            "effect_ticks": r["effect_ticks"],
            "ci_low": r["ci_low"],
            "ci_high": r["ci_high"],
            "ci_half_width_ticks": half,
            "ci_excludes_zero": bool(r["ci_excludes_zero"]),
        }

    doc = {
        "finding": "power for every patched arm: the class difference in ticks with its "
                   "bootstrap 95% CI, so a clean verdict is not printed without saying what "
                   "size of effect the measurement could have resolved.",
        "reading": "The CI half-width is the resolution floor at this budget. An effect "
                   "smaller than it would not have been distinguished from zero here, which "
                   "is a bound on the measurement and not a property of the program.",
        "generator": "bin/patched_power.py, over the committed patched-arm dumps",
        # The design constants the paper's Definition 1 quotes: the size of the test, the
        # power the minimum detectable effect is computed at, and the CI level. Emitted here
        # so the paper reads them as macros rather than retyping them.
        "design": {"alpha": 0.05, "power": 0.8, "ci_level": 0.95},
        "arms": arms,
    }
    out = pathlib.Path(a.out)
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"patched_power: wrote {out.relative_to(REPO)} ({len(arms)} patched arm(s))")
    for k, v in sorted(arms.items()):
        print(f"  {k:16s} effect {v['effect_ticks']:9.3f}  CI +/-{v['ci_half_width_ticks']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
