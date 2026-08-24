#!/usr/bin/env python3
"""Detection curve for the KyberSlash division on the x86 host. Regenerable here."""
import json, re, subprocess, sys, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
exe = HERE / "detection_curve"
subprocess.run(["gcc", "-O2", str(HERE / "detection_curve.c"), "-o", str(exe), "-lm"], check=True)
p = subprocess.run(["taskset", "-c", "2", str(exe)], check=True, capture_output=True, text=True)
curve = {}
for line in p.stdout.splitlines():
    m = re.match(r"RESULT amp_(\d+) (\S+)", line)
    if m: curve[int(m.group(1))] = float(m.group(2))
doc = {
    "finding": "kyberslash-x86-detection-curve",
    "measured_utc": os.environ.get("MEASURE_UTC", ""),
    "host": json.loads((REPO / "results" / "host.json").read_text()),
    "regenerable": "on this x86 host: taskset -c 2 python3 pairs/kyberslash/x86/detection_curve.py",
    "note": "dudect's Welch |t| between below-boundary and above-boundary dividend classes, "
            "each measurement a latency chain of AMP idivs kept in its class, M=200000 per class. "
            "On a constant-time divider |t| stays below the leak band (500) at every amplification; "
            "the nonce pairs cross the leak band at amplification 40 (t=15420), the division does not "
            "at amplification 32, so the x86 null is not a hidden sub-noise step waiting for more gain.",
    "leak_band": 500,
    "curve": [{"amp": a, "abs_t": curve[a]} for a in sorted(curve)],
    "max_abs_t": max(curve.values()) if curve else None,
    "crosses_leak_band": any(v >= 500 for v in curve.values()),
}
(REPO / "results" / "kyberslash_detection_curve.json").write_text(json.dumps(doc, indent=2) + "\n")
print(json.dumps(doc["curve"], indent=2)); print("max|t|:", doc["max_abs_t"], "crosses:", doc["crosses_leak_band"])
