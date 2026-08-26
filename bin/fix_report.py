#!/usr/bin/env python3
"""Regenerate the MatrixSSL fix-verification measurement block from committed dumps.

WHY THIS EXISTS
---------------
Every number in the paper is a macro emitted by bin/regen.py, and regen reads the
fix-verification statistics out of results/fix_verification.json. That file was assembled
by hand. So the chain from committed samples to the paper's headline had one link that no
script closed: the ten MatrixSSL designs were correct, but nothing regenerated them, and a
control could only check that the dumps had not changed (STAT-1), never that the
statistics still described them.

This closes that link. It reads the ten committed dumps, re-decides each design under the
rule in force (permutation null over dudect's first-order crop ladder, bootstrap CI on the
class difference of means), and either checks the committed block or rewrites it. Both the
permutation and the bootstrap are seeded, so the pass is reproducible: --check is a real
comparison, not a re-roll.

WHAT IT ADDS
------------
A denominator. The block recorded the class difference in ticks and never what a call
costs, so "2,097 ticks" could not be read as a fraction of the operation it was measured
on, and could not be compared with the residuals the paper quotes for the other two
libraries. call_ticks is the reference (slower) class mean on the same crop the effect size
uses, and residual_fraction is the effect over it. The unit is the scalar multiplication,
NOT a signature, and it must be quoted that way: wolfSSL's residual is a fraction of a
whole signature, which is a larger denominator.

Usage:
  bin/fix_report.py --check    # compare against the committed block, exit 1 on drift
  bin/fix_report.py --write    # rewrite the block in results/fix_verification.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
DUMPS = REPO / "results" / "raw" / "matrixssl"
FV = REPO / "results" / "fix_verification.json"
PERMS = 10000
CROP_PCT = 95.0


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "bin" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_perm = _load("dudect_permute")
_ci = _load("dudect_ci")


def call_cost(cl: np.ndarray, t: np.ndarray) -> tuple[float, float]:
    """(reference call cost, class difference) in ticks, on the effect size's own crop.

    The reference is the SLOWER class mean, which for these designs is the full-length
    nonce: the arm an attacker times when no leading zero is present. Taking the slower
    class rather than the pooled mean keeps the fraction a statement about the operation
    as it runs when the secret is not short.
    """
    keep = t <= np.percentile(t, CROP_PCT)
    c, tt = cl[keep], t[keep]
    m0, m1 = tt[c == 0].mean(), tt[c == 1].mean()
    return float(max(m0, m1)), float(m1 - m0)


def design(path: pathlib.Path) -> dict:
    p = _perm.permute(path, perms=PERMS)
    if "error" in p:
        raise SystemExit(f"{path.name}: {p['error']}")
    cl, t = _ci.load(path)
    eff = _ci.analyse(cl, t, crop_pct=CROP_PCT)
    ref, diff = call_cost(cl, t)
    if eff["effect_ticks"] is None:
        raise SystemExit(f"{path.name}: no effect sample")
    # The two routes to the class difference must agree, or one of them is not measuring
    # what it says. They share a crop but not a code path.
    if abs(diff - eff["effect_ticks"]) > 1e-6:
        raise SystemExit(f"{path.name}: effect size disagrees between routes "
                         f"({diff} vs {eff['effect_ticks']})")
    return {
        "ci_excludes_zero": bool(eff["ci_excludes_zero"]),
        "ci_high": eff["ci_high"],
        "ci_low": eff["ci_low"],
        "effect_ticks": eff["effect_ticks"],
        "max_abs_t": p["observed_max_abs_t"],
        "measurements": p["measurements"],
        "n_at_argmax": p["n_at_argmax_test"],
        "permutation_p": p["p_value"],
        "permutations": p["permutations"],
        "call_ticks": ref,
        "residual_fraction": abs(eff["effect_ticks"]) / ref,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    a = ap.parse_args()

    dumps = sorted(DUMPS.glob("*.bin.gz"))
    if not dumps:
        print("fix_report: no committed dumps under results/raw/matrixssl", file=sys.stderr)
        return 2
    fresh = {d.name.replace(".bin.gz", ""): design(d) for d in dumps}

    doc = json.loads(FV.read_text())
    block = doc["libraries"]["matrixssl"]["measurements_full_report"]
    old = block.get("designs", {})

    if a.check:
        drift = []
        if set(old) != set(fresh):
            drift.append(f"design set differs: committed {sorted(old)} vs computed {sorted(fresh)}")
        for name in sorted(set(old) & set(fresh)):
            for k, v in fresh[name].items():
                if k in ("call_ticks", "residual_fraction"):
                    continue                       # added by this generator
                w = old[name].get(k)
                if isinstance(v, float) and isinstance(w, (int, float)):
                    if abs(v - w) > max(1e-9, abs(v) * 1e-9):
                        drift.append(f"{name}.{k}: committed {w} vs computed {v}")
                elif w != v:
                    drift.append(f"{name}.{k}: committed {w!r} vs computed {v!r}")
        if drift:
            print("fix_report: the committed block no longer matches the dumps")
            for d in drift:
                print(f"  - {d}")
            return 1
        print(f"fix_report: {len(fresh)} design(s) reproduce the committed block exactly")
        return 0

    block["designs"] = fresh
    block["generator"] = "bin/fix_report.py --write, over results/raw/matrixssl/*.bin.gz"
    FV.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"fix_report: wrote {len(fresh)} design(s) to {FV.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
