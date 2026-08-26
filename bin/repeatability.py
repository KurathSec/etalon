#!/usr/bin/env python3
"""What the arms acquired twice agree on, and on which of them it is a re-run.

CORRECTED 2026-08-26. An earlier revision of this file claimed the second acquisition
was "the same binary, at the same budget" as the committed dump. That is false for
most of these arms, and the paper repeated it. The detection curve runs each pair at
amplification factor 1, and the dudect adapter turns that into `-DAMP=1` on the
compile, which OVERRIDES the pair's compiled-in default: 40 for the ECDSA pairs, 200
for the rejection sampler, 1200 for the message pair. Where a pair's AMP lives in a
source that arm compiles, the re-acquisition is a REBUILD AT A DIFFERENT GAIN, not a
re-run, and its effect size is not comparable with the committed one. The committed
message pair reads -74,545 ticks against -33 on the factor-one rebuild.

So each arm is classified. `same_binary` is true only where no source that arm
compiles carries an AMP define, which is both division-pair arms and the patched arms
of the two ECDSA pairs, whose AMP is in vulnerable.c alone.

What the whole set supports is that the VERDICT does not turn on the gain or on the
run. What only the same-binary arms support is a comparison of effect estimates, and
the effect comparison below is restricted to them. Those arms DO each give one gap
between two acquisitions of one binary, which this file records; what they do not give
is a RANGE, which needs more repeats and exists in this corpus only for the
fix-verification case (results/matrixssl_repeats.json).
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIRS = ROOT / "pairs"


def same_binary(pair: str, arm: str) -> bool:
    """True when -DAMP=1 cannot change this arm's binary.

    The adapter compiles the arm's own source plus the pair's extra sources. If none
    of them mentions AMP, the define is inert and the factor-one build is byte-for-byte
    the committed one. If any does, the rebuild is a different binary.
    """
    src = PAIRS / pair / "src"
    if not src.is_dir():
        return False
    # The arm's own file, plus any shared source the pair carries. Shared work.c is the
    # case that makes BOTH arms of the message pair differ.
    files = [f for f in src.glob("*.c")
             if f.stem == arm or f.stem not in ("vulnerable", "patched")]
    return not any("AMP" in f.read_text(errors="replace") for f in files)
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
        sb = same_binary(pair, arm)
        row = {
            "pair": pair,
            "arm": arm,
            "same_binary": sb,
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
        if arm == "patched" and pair in power and sb:
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
            "CORRECTED 2026-08-26. An earlier revision of this field said the "
            "factor-one rows are 'the default build at the committed budget', which is "
            "false for most of these arms: the adapter compiles them with -DAMP=1, "
            "overriding each pair's compiled-in default, so where a pair's AMP is in a "
            "source the arm compiles the second acquisition is a rebuild at a different "
            "gain. Only the division pair's two arms and the patched arms of the two "
            "ECDSA pairs are the same binary, and same_binary records which."
        ),
        "reading": (
            "The verdict comparison spans all ten arms and shows the verdict does not "
            "turn on the gain or on the run. The EFFECT comparison spans only the "
            "same-binary arms, because an effect measured at amplification one is not "
            "comparable with one measured at forty or twelve hundred; the committed "
            "message pair reads -74,545 ticks against -33 on the factor-one rebuild. "
            "The same-binary arms DO give one gap each between two acquisitions of one "
            "binary, which this file records; what they do not give is a range, which "
            "needs more repeats and exists in this corpus only for the fix-verification "
            "case, in results/matrixssl_repeats.json. An earlier revision of this field "
            "said neither comparison bounds between-acquisition spread at all, which "
            "understated what the same-binary arms measure."
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
        # The prose fields are checked too, and they are the ones that went stale: this
        # check compared seven integers, so a generator whose `reading` was edited to
        # withdraw a claim could sit beside a committed record still asserting it, and
        # the paper cites the record by name. A count is not the only thing that drifts.
        bad = [
            k
            for k in ("n_arms", "n_status_agree", "n_status_disagree",
                      "n_effect_compared", "n_effect_mutually_inside",
                      "n_gap_below_coarser_half_width",
                      "n_gap_below_finer_half_width",
                      "finding", "why", "reading", "generator")
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
