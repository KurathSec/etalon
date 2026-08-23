#!/usr/bin/env python3
"""varlat adapter: the KyberSlash patched Valgrind, detecting variable-latency
instructions on secret data.

Poisons the secret, enables TIMECOP mode, runs the entry once under the patched
memcheck, and parses the report by its `what` text (`Variable-latency instruction
operand`), NOT the kind, which stays UninitValue. Emits a normalised verdict;
never trusts the exit code.
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
IMAGE = "localhost/ct-toolchain/varlat:1"
DRIVER = REPO / "src" / "corpus" / "score" / "adapters"
CPU = 2


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 600) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "varlat.toml").read_text())
    driver, header = cfg["driver"], cfg["header"]
    opt = opt or cfg.get("opt", "Os")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    libs = cfg.get("libs", "")
    result = subprocess.run(
        ["podman", "run", "--rm", "--network=none",
         "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
         "-v", f"{DRIVER}:/driver:ro,Z", IMAGE, "sh", "-c",
         f"cp /src/{header} /work/ && "
         f"gcc -{opt} -g -I/opt/varlat/include -I/work -I/harness -o /work/d "
         f"/driver/{driver} /src/{arm}.c {extra} {libs} 2>/work/cc.err "
         f"|| {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}; "
         f"taskset -c {CPU} valgrind --tool=memcheck --xml=yes "
         f"--xml-file=/work/vg.xml --error-exitcode=0 /work/d >/dev/null 2>/work/vg.err; "
         f"cat /work/vg.xml"],
        capture_output=True, text=True, timeout=timeout)

    if "BUILD_FAILED" in result.stdout or result.returncode == 3:
        return {"adapter": "varlat", "tool": "varlat", "arm": arm, "opt": opt,
                "status": "error", "detail": "driver build failed",
                "host": {"kernel": platform.release(), "machine": platform.machine()}}

    xml = result.stdout
    # Match the varlat report by its what-text, not the kind (which stays UninitValue).
    whats = re.findall(r"<what>([^<]*)</what>", xml)
    varlat_hits = [w for w in whats if "Variable-latency instruction operand" in w]
    other_uninit = [w for w in whats if "uninitialised" in w.lower()
                    and "Variable-latency" not in w]
    if "VARLAT_DONE" not in result.stdout and not xml.strip():
        status, detail = "error", "no valgrind output"
    elif varlat_hits:
        status, detail = "leak_reported", "variable-latency instruction on secret data"
    elif other_uninit:
        # A plain uninit-value report without a variable-latency finding: the
        # secret reached a branch or index, not a variable-latency op. Still a
        # leak, but of a different mechanism; record it distinctly.
        status, detail = "leak_reported", "uninitialised-value use (non-varlat)"
    else:
        status, detail = "clean", "no variable-latency instruction on secret data"
    return {"adapter": "varlat", "tool": "varlat", "arm": arm, "opt": opt,
            "status": status, "detail": detail,
            "varlat_hits": len(varlat_hits),
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
