#!/usr/bin/env python3
"""Between-acquisition agreement for the arms acquired twice.

The detection curve of bin/detection_curve_all.py runs each pair at amplification
factor 1, which is the default build: the same binary, at the same budget, as the
committed corpus dump. Those rows are therefore a second, independent acquisition
of ten arms, and this script says what the two acquisitions agree on.

Two acquisitions per arm is a consistency check, not a variance estimate. It cannot
bound between-acquisition spread; it can show whether the verdict and the sign of
the effect survive a re-run, and whether each acquisition's point estimate lands
inside the other's within-acquisition interval.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CURVE = ROOT / "results" / "detection_curve_all.json"
POWER = ROOT / "results" / "patched_power.json"
VERDICTS = ROOT / "results" / "verdicts.jsonl"
OUT = ROOT / "results" / "repeatability.json"

_EFFECT = re.compile(
    r"effect (-?[\d.]+) ticks, 95% CI \[(-?[\d.]+), (-?[\d.]+)\]"
)


def _curve_rows():
    d = json.loads(CURVE.read_text())
    rows = {}
    for r in d["rows"]:
        if r["amp"] != 1:
            continue
        m = _EFFECT.search(r["detail"])
        if not m:
            sys.exit(f"no effect in detail for {r['pair']}/{r['arm']}")
        lo, hi = float(m.group(2)), float(m.group(3))
        rows[(r["pair"], r["arm"])] = {
            "status": r["status"],
            "effect_ticks": float(m.group(1)),
            "ci_low": lo,
            "ci_high": hi,
            "ci_half_width_ticks": (hi - lo) / 2.0,
        }
    return rows


def _committed_status():
    """The committed verdict per (pair, arm), as dudect recorded it."""
    out = {}
    for line in VERDICTS.read_text().splitlines():
        if not line.strip():
            continue
        v = json.loads(line)
        if v.get("tool") != "dudect":
            continue
        for arm in ("vulnerable", "patched"):
            s = v.get(f"{arm}_status")
            if s:
                out[(v["pair"], arm)] = s
    return out


def main() -> int:
    check = "--check" in sys.argv
    curve = _curve_rows()
    committed_status = _committed_status()
    power = json.loads(POWER.read_text())["arms"]

    arms, agree, disagree = [], 0, 0
    inside = 0
    n_effect_pairs = 0
    for (pair, arm), re_acq in sorted(curve.items()):
        first = committed_status.get((pair, arm))
        row = {
            "pair": pair,
            "arm": arm,
            "committed_status": first,
            "reacquired_status": re_acq["status"],
            "status_agrees": first == re_acq["status"],
            "reacquired_effect_ticks": re_acq["effect_ticks"],
            "reacquired_ci_half_width_ticks": re_acq["ci_half_width_ticks"],
        }
        if first is None:
            row["note"] = "no committed dudect row for this arm"
        else:
            agree += row["status_agrees"]
            disagree += not row["status_agrees"]
        # The committed effect estimate exists only for the patched arms, which
        # are the ones bin/patched_power.py reports on.
        if arm == "patched" and pair in power:
            c = power[pair]
            row["committed_effect_ticks"] = c["effect_ticks"]
            row["committed_ci_half_width_ticks"] = c["ci_half_width_ticks"]
            row["gap_ticks"] = abs(c["effect_ticks"] - re_acq["effect_ticks"])
            row["reacquired_inside_committed_ci"] = (
                c["ci_low"] <= re_acq["effect_ticks"] <= c["ci_high"]
            )
            row["committed_inside_reacquired_ci"] = (
                re_acq["ci_low"] <= c["effect_ticks"] <= re_acq["ci_high"]
            )
            n_effect_pairs += 1
            inside += (
                row["reacquired_inside_committed_ci"]
                and row["committed_inside_reacquired_ci"]
            )
        arms.append(row)

    gaps = [r["gap_ticks"] for r in arms if "gap_ticks" in r]
    halves = [
        max(r["committed_ci_half_width_ticks"], r["reacquired_ci_half_width_ticks"])
        for r in arms
        if "gap_ticks" in r
    ]
    # Is the move between the two acquisitions smaller than what an acquisition
    # could resolve? Against the coarser of the two, and against the finer.
    for r in arms:
        if "gap_ticks" not in r:
            continue
        hw = (r["committed_ci_half_width_ticks"], r["reacquired_ci_half_width_ticks"])
        r["gap_below_coarser_half_width"] = r["gap_ticks"] < max(hw)
        r["gap_below_finer_half_width"] = r["gap_ticks"] < min(hw)
    n_below_coarser = sum(
        r.get("gap_below_coarser_half_width", False) for r in arms
    )
    n_below_finer = sum(r.get("gap_below_finer_half_width", False) for r in arms)
    doc = {
        "finding": (
            "the arms acquired twice, and what the second acquisition agrees with"
        ),
        "why": (
            "Every per-arm interval in this paper comes from one acquisition and "
            "bounds sampling within it. The detection curve re-runs five pairs at "
            "amplification factor 1, which is the default build at the committed "
            "budget, so ten arms have a second independent acquisition."
        ),
        "reading": (
            "Two acquisitions is n=2. It does not estimate between-acquisition "
            "spread and no interval here is widened by it. What it shows is that "
            "the verdict and the sign of the effect survived a re-run, and where "
            "the two point estimates landed relative to each other's "
            "within-acquisition interval."
        ),
        "generator": "bin/repeatability.py",
        "n_arms": len(arms),
        "n_status_compared": agree + disagree,
        "n_status_agree": agree,
        "n_status_disagree": disagree,
        "n_effect_compared": n_effect_pairs,
        "n_effect_mutually_inside": inside,
        "n_gap_below_coarser_half_width": n_below_coarser,
        "n_gap_below_finer_half_width": n_below_finer,
        "max_gap_ticks": max(gaps) if gaps else None,
        "max_ci_half_width_ticks": max(halves) if halves else None,
        "arms": arms,
    }

    if check:
        if not OUT.exists():
            print("repeatability: results/repeatability.json missing", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text())
        bad = [
            k
            for k in ("n_arms", "n_status_agree", "n_status_disagree",
                      "n_effect_compared", "n_effect_mutually_inside",
                      "n_gap_below_coarser_half_width",
                      "n_gap_below_finer_half_width")
            if old.get(k) != doc[k]
        ]
        if bad:
            print(f"repeatability: {', '.join(bad)} differ from committed",
                  file=sys.stderr)
            return 1
        print(f"repeatability: check clean ({doc['n_arms']} arms)")
        return 0

    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(
        f"repeatability: {doc['n_status_agree']}/{doc['n_status_compared']} verdicts "
        f"agree, {doc['n_effect_mutually_inside']}/{doc['n_effect_compared']} effect "
        f"estimates mutually inside, max gap {doc['max_gap_ticks']:.3f} ticks "
        f"vs max half-width {doc['max_ci_half_width_ticks']:.3f}; "
        f"gap below the coarser half-width in "
        f"{doc['n_gap_below_coarser_half_width']}/{doc['n_effect_compared']}, "
        f"below the finer in {doc['n_gap_below_finer_half_width']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
