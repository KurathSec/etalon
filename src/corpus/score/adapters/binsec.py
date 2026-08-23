#!/usr/bin/env python3
"""binsec adapter: Binsec/Rel2 relational symbolic execution, checking a binary
for constant-time violations (control-flow, memory-access, and the experimental
divisor/dividend classes).

The tool analyses an ELF, not source, and marks secrets by symbol name in an SSE
script (`secret global s`). So each pair ships a binsec driver that declares its
secret and public inputs as named globals and calls the arm's function from a
main that halts at <exit>. The image has no gcc, so the ELF is built in a gcc
cell and analysed in the binsec cell over a shared work dir.

Verdict mapping is the one frozen in PR-1: `insecure` is a leak, `secure` is
clean, and `unknown`, a solver timeout or a depth cut is INCONCLUSIVE
(budget_exhausted), never folded into clean. The exit code is never the verdict;
the `Program status is` line is.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[4]
BUILD_IMAGE = "localhost/ct-toolchain/gcc-bookworm:1"
# Pinned by digest, frozen for PR-1 (locks/images.lock.toml).
BINSEC_IMAGE = ("docker.io/binsec/binsec@sha256:"
                "2a51e455f055874d71cbf030a778e8be19455876bcd57c1845c163fed6fc482f")
DRIVER = REPO / "src" / "corpus" / "score" / "adapters"


def _cfg_text(cfg: dict) -> str:
    lines = [f"starting from <{cfg.get('entry', 'main')}>",
             "with concrete stack pointer"]
    secret = cfg.get("secret_globals", [])
    public = cfg.get("public_globals", [])
    if secret:
        lines.append("secret global " + ", ".join(secret))
    if public:
        lines.append("public global " + ", ".join(public))
    for a in cfg.get("assume", []):
        lines.append(f"assume {a}")
    lines.append(f"halt at <{cfg.get('halt', 'exit')}>")
    lines.append("explore all")
    return "\n".join(lines) + "\n"


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 600) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "binsec.toml").read_text())
    driver, header = cfg["driver"], cfg.get("header")
    opt = opt or cfg.get("opt", "O2")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    libs = cfg.get("libs", "")
    features = cfg.get("features", "memory-access,control-flow")
    depth = int(cfg.get("depth", 100000))
    solver_timeout = int(cfg.get("sse_timeout", 120))
    host = {"kernel": platform.release(), "machine": platform.machine()}

    with tempfile.TemporaryDirectory(prefix="binsec-") as td:
        work = pathlib.Path(td)
        (work / "check.cfg").write_text(_cfg_text(cfg), encoding="utf-8")

        build = subprocess.run(
            ["podman", "run", "--rm", "--network=none",
             "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
             "-v", f"{DRIVER}:/driver:ro,Z", "-v", f"{work}:/work:rw,Z",
             BUILD_IMAGE, "sh", "-c",
             (f"cp /src/{header} /work/ 2>/dev/null; " if header else "") +
             f"gcc -{opt} -g -static -no-pie -I/work -I/harness -I/src "
             f"-o /work/d /driver/{driver} /src/{arm}.c {extra} {libs} "
             f"2>/work/cc.err || {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}"],
            capture_output=True, text=True, timeout=timeout)
        if "BUILD_FAILED" in build.stdout or build.returncode == 3:
            return {"adapter": "binsec", "tool": "binsec", "arm": arm, "opt": opt,
                    "status": "error", "detail": "driver build failed",
                    "cc_err": build.stdout[-800:], "host": host}

        run = subprocess.run(
            # --user 0: the image's non-root default user cannot traverse the
            # 0700 work dir the gcc cell wrote as the host uid. Rootless, so
            # container root is still the unprivileged host user.
            ["podman", "run", "--rm", "--network=none", "--user", "0",
             "-v", f"{work}:/work:rw,Z", BINSEC_IMAGE, "sh", "-c",
             f"cd /work && binsec -sse -checkct "
             f"-checkct-features {features} -checkct-leak-info instr "
             f"-sse-script check.cfg -sse-depth {depth} "
             f"-sse-timeout {solver_timeout} d 2>&1"],
            capture_output=True, text=True, timeout=timeout)

    out = run.stdout
    m = re.search(r"Program status is\s*:\s*(secure|insecure|unknown)", out)
    leaks = re.findall(r"Instruction (0x[0-9a-f]+) has (.+?) leak", out)
    incomplete = "Exploration is incomplete" in out
    if m is None:
        status, detail = "error", "no checkct status line"
    elif m.group(1) == "insecure":
        status, detail = "leak_reported", f"{len(leaks)} leaky instruction(s)"
    elif m.group(1) == "unknown" or incomplete:
        # A solver-unknown, a timeout or a depth cut is no evidence, not evidence
        # of absence. PR-1 maps it to INCONCLUSIVE, never to clean.
        status, detail = "budget_exhausted", "status unknown or exploration incomplete"
    else:
        status, detail = "clean", "proven secure over the explored inputs"
    return {"adapter": "binsec", "tool": "binsec", "arm": arm, "opt": opt,
            "status": status, "detail": detail,
            "binsec_status": m.group(1) if m else None,
            "leaks": [{"at": a, "kind": k} for a, k in leaks],
            "features": features, "host": host}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--arm", required=True, choices=["vulnerable", "patched"])
    a = ap.parse_args()
    if not shutil.which("podman"):
        print(json.dumps({"status": "error", "detail": "podman not found"}))
        return 2
    print(json.dumps(score(REPO / "pairs" / a.pair, a.arm), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
