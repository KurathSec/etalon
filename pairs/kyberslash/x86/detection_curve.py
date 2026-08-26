#!/usr/bin/env python3
"""Detection curve for the KyberSlash division on the x86 host. Regenerable here."""
import json, re, subprocess, sys, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
exe = HERE / "detection_curve"
# M must match detection_curve.c's per-class measurement count, and the band is the
# same calibrated null the scoring adapter uses, so the figure and the verdict rule
# cannot drift apart.
M = int(re.search(r"#define\s+M\s+(\d+)", (HERE / "detection_curve.c").read_text()).group(1))
PERMS = int(re.search(r"#define\s+PERMS\s+(\d+)",
                      (HERE / "detection_curve.c").read_text()).group(1))
subprocess.run(["gcc", "-O2", str(HERE / "detection_curve.c"), "-o", str(exe), "-lm"], check=True)

# R independent repetitions of the whole curve. One run of this experiment is not a
# result: repeated on the same host it gives |t| = 36 at one amplification and |t| = 0.3
# at the same amplification minutes later, with the sign of the mean difference flipping.
# A single run therefore reports whichever way the noise fell. What is reportable is the
# distribution: if a per-division step were real, the sign of the mean difference would
# agree across runs and the per-division magnitude would hold as amplification grows.
R = int(os.environ.get("CURVE_RUNS", "5"))
runs = []
for r in range(R):
    out = subprocess.run(["taskset", "-c", "2", str(exe)], check=True,
                         capture_output=True, text=True).stdout
    one = {}
    for line in out.splitlines():
        m = re.match(r"RESULT amp_(\d+) (\S+) p (\S+) mean (\S+) perdiv (\S+)", line)
        if m:
            one[int(m.group(1))] = {"abs_t": float(m.group(2)), "p": float(m.group(3)),
                                    "mean_ticks": float(m.group(4)),
                                    "ticks_per_division": float(m.group(5))}
    runs.append(one)

amps = sorted(runs[0])
def agg(a, key):
    return [runs[r][a][key] for r in range(R)]

curve = []
for a in amps:
    ts, ps, ms = agg(a, "abs_t"), agg(a, "p"), agg(a, "mean_ticks")
    pos = sum(1 for m in ms if m > 0)
    curve.append({
        "amp": a,
        "abs_t_runs": [round(x, 3) for x in ts],
        "abs_t_min": round(min(ts), 3), "abs_t_max": round(max(ts), 3),
        "p_runs": ps,
        "runs_significant_raw": sum(1 for x in ps if x <= 0.05),
        "mean_ticks_runs": [round(x, 5) for x in ms],
        "mean_sign_positive_runs": pos,
        "sign_consistent": pos == R or pos == 0,
        "ticks_per_division_runs": [round(x, 6) for x in agg(a, "ticks_per_division")],
    })

sign_consistent = [c["amp"] for c in curve if c["sign_consistent"]]
always_sig = [c["amp"] for c in curve if c["runs_significant_raw"] == R]
doc = {
    "finding": "kyberslash-x86-detection-curve",
    "measured_utc": os.environ.get("MEASURE_UTC", ""),
    "host": json.loads((REPO / "results" / "host.json").read_text()),
    "regenerable": "on this x86 host: taskset -c 2 python3 pairs/kyberslash/x86/detection_curve.py",
    "design": ("Paired: a below-boundary and an above-boundary dividend timed back to "
               "back, which of the two goes first decided by a coin flip per iteration "
               "so measurement order cannot masquerade as operand dependence. Each "
               "measurement is a latency chain of AMP divisions. The per-run decision is "
               "a SIGN-FLIP permutation null over the paired differences, the exact null "
               "this design licenses; no band calibrated on another harness is used. "
               "%d measurements per class per run, %d repetitions of the whole curve."
               % (M, R)),
    "why_repetitions": ("Because one run of this is not reproducible. The same "
                        "amplification gives a large statistic in one run and nothing in "
                        "the next, so a single run reports the noise rather than the "
                        "divider. Only quantities stable across repetitions are read as "
                        "findings here."),
    "measurements_per_class": M,
    "runs": R,
    "permutations_per_point": PERMS,
    "curve": curve,
    "amps_with_consistent_sign": sign_consistent,
    "amps_significant_in_every_run": always_sig,
    "reading": ("A per-division operand-dependent step would show a mean difference of "
                "one sign in every run and a per-division magnitude that does not shrink "
                "as the chain lengthens. Read the sign-consistency and the "
                "ticks_per_division columns, not any single |t|."),
}
(REPO / "results" / "kyberslash_detection_curve.json").write_text(json.dumps(doc, indent=2) + "\n")
for c in curve:
    print(f"amp={c['amp']:3d} |t| {c['abs_t_min']:8.3f}..{c['abs_t_max']:8.3f}  "
          f"sig {c['runs_significant_raw']}/{R}  sign+ {c['mean_sign_positive_runs']}/{R}  "
          f"consistent={c['sign_consistent']}")
print("sign-consistent amps:", sign_consistent)
print("significant in every run:", always_sig)
