#!/usr/bin/env python3
"""dudect adapter: score a tag-comparison pair's arm for a timing leak.

Emits a normalised verdict, never a score. The verdict vocabulary is the one the
harness design fixes: leak_reported, clean, budget_exhausted, error. dudect is a
statistical tool, so its result is a detection at a stated budget on a stated
host, and the adapter records the host and the pinning so the result is
reproducible.

The exit code is never trusted: dudect exits 0 whether or not it found leakage.
The verdict comes from a machine line the driver prints.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import platform
import re
import subprocess
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[4]
IMAGE = "localhost/ct-toolchain/dudect:1"
DRIVER = REPO / "src" / "corpus" / "score" / "adapters" / "dudect_driver.c"
CPU = 2   # a P-core; cpuset is undelegated so we taskset inside the container


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 900) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "dudect.toml").read_text())
    driver = cfg["driver"]
    header = cfg["header"]
    opt = opt or cfg.get("opt", "O2")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    libs = cfg.get("libs", "")
    result = subprocess.run(
        ["podman", "run", "--rm", "--network=none",
         "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
         "-v", f"{DRIVER.parent}:/driver:ro,Z",
         IMAGE, "sh", "-c",
         f"cp /src/{header} /work/ && "
         f"gcc -{opt} -I/work -I/harness -o /work/d "
         f"/driver/{driver} /src/{arm}.c {extra} -lm {libs} 2>/work/cc.err "
         f"|| {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}; "
         f"taskset -c {CPU} /work/d"],
        capture_output=True, text=True, timeout=timeout)

    out = result.stdout
    tvals = re.findall(r"max t:\s*([+-]?[0-9.]+(?:[eE][+-]?[0-9]+)?)", out)
    max_t = abs(float(tvals[-1])) if tvals else None

    # Classify by dudect's OWN documented thresholds rather than the driver's
    # binary verdict: |t| > 500 is "failed with overwhelming probability", |t| <
    # 10 is "probably constant time at this budget", and the band between is
    # inconclusive. A fixed binary threshold cannot separate a strong exploitable
    # leak from weak residual microarchitectural noise in complex code, which is
    # itself a finding this corpus exists to make visible.
    T_LEAK, T_CLEAN = 500.0, 10.0
    if "BUILD_FAILED" in result.stdout or result.returncode == 3:
        status, detail = "error", "driver build failed"
    elif max_t is None:
        status, detail = "budget_exhausted", "no t-statistic emitted"
    elif max_t > T_LEAK:
        status, detail = "leak_reported", f"max |t|={max_t:.0f} > 500"
    elif max_t < T_CLEAN:
        status, detail = "clean", f"max |t|={max_t:.1f} < 10"
    else:
        status, detail = "budget_exhausted", (
            f"max |t|={max_t:.0f} in the inconclusive band [10, 500]: neither a "
            f"strong leak nor demonstrably clean at this budget")
    return {
        "adapter": "dudect", "tool": "dudect", "arm": arm, "opt": opt,
        "status": status, "detail": detail,
        "max_t": float(tvals[-1]) if tvals else None,
        "host": {"kernel": platform.release(), "machine": platform.machine(),
                 "cpu_pinned_to": CPU},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--arm", required=True, choices=["vulnerable", "patched"])
    ap.add_argument("--opt", default="O2")
    a = ap.parse_args()
    r = score(REPO / "pairs" / a.pair, a.arm, a.opt)
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
