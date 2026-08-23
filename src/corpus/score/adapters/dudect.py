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
    result = subprocess.run(
        ["podman", "run", "--rm", "--network=none",
         "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
         "-v", f"{DRIVER.parent}:/driver:ro,Z",
         IMAGE, "sh", "-c",
         f"cp /src/{header} /work/ && "
         f"gcc -{opt} -I/work -I/harness -o /work/d "
         f"/driver/{driver} /src/{arm}.c {extra} -lm 2>/work/cc.err "
         f"|| {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}; "
         f"taskset -c {CPU} /work/d"],
        capture_output=True, text=True, timeout=timeout)

    out = result.stdout
    m = re.search(r"DUDECT_VERDICT (LEAK|NO_LEAK_EVIDENCE)", out)
    if "BUILD_FAILED" in result.stdout or result.returncode == 3:
        status = "error"
        detail = "driver build failed"
    elif m is None:
        # No verdict line and no build failure: the tool ran but produced nothing
        # we can key on. That is budget_exhausted (it did not conclude), not clean.
        status = "budget_exhausted"
        detail = "no verdict line emitted"
    elif m.group(1) == "LEAK":
        status = "leak_reported"
        detail = "distributions differ"
    else:
        status = "clean"
        detail = "no leakage evidence at the measurement budget"

    # dudect prints its running max-t; capture the last one for the record.
    tvals = re.findall(r"max t:\s*([+-]?[0-9.]+(?:[eE][+-]?[0-9]+)?)", out)
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
