#!/usr/bin/env python3
"""TIMECOP adapter: valgrind memcheck as a constant-time checker.

Poisons the secret and runs the entry once under memcheck. A conditional-jump or
memory access on uninitialised (secret) data is reported. Parses valgrind's XML,
never the exit code, and matches the `kind`, distinguishing a branch on secret
(UninitCondition) from a memory index on secret (UninitValue). Emits a normalised
verdict.
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
IMAGE = "localhost/ct-toolchain/timecop:1"
DRIVER = REPO / "src" / "corpus" / "score" / "adapters"
CPU = 2


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 600) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "timecop.toml").read_text())
    driver = cfg["driver"]; header = cfg["header"]
    opt = opt or cfg.get("opt", "O2")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    result = subprocess.run(
        ["podman", "run", "--rm", "--network=none",
         "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
         "-v", f"{DRIVER}:/driver:ro,Z",
         IMAGE, "sh", "-c",
         f"cp /src/{header} /work/ && "
         f"gcc -{opt} -g -I/work -I/harness -o /work/d "
         f"/driver/{driver} /src/{arm}.c {extra} 2>/work/cc.err "
         f"|| {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}; "
         f"taskset -c {CPU} valgrind --tool=memcheck --xml=yes "
         f"--xml-file=/work/vg.xml --error-exitcode=0 /work/d >/dev/null 2>/work/vg.err; "
         f"cat /work/vg.xml"],
        capture_output=True, text=True, timeout=timeout)

    if "BUILD_FAILED" in result.stdout or result.returncode == 3:
        return {"adapter": "timecop", "tool": "timecop", "arm": arm, "opt": opt,
                "status": "error", "detail": "driver build failed",
                "host": {"kernel": platform.release(), "machine": platform.machine()}}

    xml = result.stdout
    kinds = re.findall(r"<kind>(\w+)</kind>", xml)
    leak_kinds = [k for k in kinds if k.startswith("Uninit")]
    if "TIMECOP_DONE" not in result.stdout and not xml.strip():
        status, detail = "error", "no valgrind output"
    elif leak_kinds:
        status, detail = "leak_reported", f"memcheck: {','.join(sorted(set(leak_kinds)))}"
    else:
        status, detail = "clean", "no uninitialised-value use on secret data"
    return {"adapter": "timecop", "tool": "timecop", "arm": arm, "opt": opt,
            "status": status, "detail": detail,
            "leak_kinds": sorted(set(leak_kinds)),
            "host": {"kernel": platform.release(), "machine": platform.machine(),
                     "cpu_pinned_to": CPU}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--arm", required=True, choices=["vulnerable", "patched"])
    a = ap.parse_args()
    print(json.dumps(score(REPO / "pairs" / a.pair, a.arm), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
