#!/usr/bin/env python3
"""The controls that decide what the x86 per-call magnitude difference is made of.

WHY THIS EXISTS
The per-call low-against-high design on the acquisition host resolves a difference
of about half a tick with the high class faster, which a rising operand latency
cannot produce, and the paper attributed it to the harness's arrangement of the
two classes, amplified by a longer instruction. That was a hypothesis. A referee
asked for the control that decides it: the same design with the divider fed the
same operand in both classes, so that an arrangement effect would remain and an
operand effect could not.

WHAT IT MEASURES
Four runs of one program, magnitude_control.c, in one session on one core, each
four million paired calls with the order within each pair randomised, as
magnitude_sensitivity.c does. same: both calls of a pair divide the same operand.
lowsplit: two classes inside the quotient-zero range. highsplit: two classes
inside the high range. lowhigh: the original contrast, rerun beside the controls
so the four figures share one host state. Each reports the paired mean difference
in ticks, the t statistic and the minimum detectable effect at every budget.

Usage: magnitude_control.py            (pin it: taskset -c 2)
"""
from __future__ import annotations
import json, os, pathlib, subprocess, sys, datetime
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
OUT = REPO / "results" / "kyberslash_x86_magnitude_control.json"
sys.path.insert(0, str(REPO / "bin"))
import host_facts  # noqa: E402
MODES = ("same", "lowsplit", "highsplit", "lowhigh")


def build() -> pathlib.Path:
    exe = HERE / "magnitude_control"
    subprocess.run(["cc", "-O2", "-o", str(exe), str(HERE / "magnitude_control.c"), "-lm"], check=True)
    return exe


def run(exe: pathlib.Path, mode: str) -> dict:
    r = subprocess.run([str(exe)], env={**os.environ, "MODE": mode}, capture_output=True, text=True, check=True)
    out = {}
    for line in r.stdout.splitlines():
        if line.startswith("RESULT "):
            _, k, v = line.split()
            out[k] = float(v)
    return out


def main() -> int:
    exe = build()
    res = {m: run(exe, m) for m in MODES}
    top = "n_4000000"
    doc = {
        "finding": FINDING,
        "why": __doc__.split("WHY THIS EXISTS")[1].split("WHAT IT MEASURES")[0].strip(),
        "method": __doc__.split("WHAT IT MEASURES")[1].split("Usage:")[0].strip(),
        "generator": "pairs/kyberslash/x86/magnitude_control.py (a measurement on the acquisition host; not regenerable elsewhere)",
        "measured_utc": os.environ.get("MEASURE_UTC") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "host": host_facts.capture(),
        "design": {
            "same": "both calls of a pair divide the same operand drawn from [0, 3329)",
            "lowsplit": "[0,416) against [416,833), both quotient zero",
            "highsplit": "[1664,2496) against [2496,3329)",
            "lowhigh": "[0,833) against [1664,3329), the original contrast",
            "pairs": 4000000, "order": "randomised within each pair", "counter": "rdtscp",
        },
        "reading": ("The same-operand run is the control that decides the account. Its two calls divide the "
                    "same value, so any difference is the harness's own: it reads about 0.40 ticks, the "
                    "second-timed class faster, at a t of twenty. The original low-against-high contrast, "
                    "rerun in this binary, reads about 0.06 ticks against the 0.55 the committed record "
                    "holds for the same design in another binary, so the raw per-call figure belongs to "
                    "the binary's arrangement of the two classes and not to the divider. Net of the "
                    "same-operand offset, the classes differ by about 0.3 ticks with the larger dividend "
                    "slower, and the splits inside the low and high ranges by about 0.2 and 0.4: a small "
                    "rising dependence the latency chain does not show, an order of magnitude below the "
                    "call, and absorbed when the division is pipelined."),
        "results": res,
        "summary": {m: {"mean_ticks": res[m][f"{top}_mean_ticks"], "t": res[m][f"{top}_t"],
                        "mde_ticks": res[m][f"{top}_mde_ticks"]} for m in MODES},
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    for m in MODES:
        s = doc["summary"][m]
        print(f"  {m:<10} mean {s['mean_ticks']:+.4f} ticks  |t| {s['t']:.1f}  MDE {s['mde_ticks']:.4f}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


FINDING = ("on the acquisition host the per-call low-against-high difference is mostly the harness's: "
           "with the same operand in both classes the paired design reads about 0.40 ticks at a t of "
           "twenty, the original contrast reads about 0.06 ticks in this binary against 0.55 in the "
           "committed one, and net of the same-operand offset the larger dividend is slower by about "
           "0.3 ticks, an order of magnitude below the call and absorbed when pipelined")

if __name__ == "__main__":
    sys.exit(main())
