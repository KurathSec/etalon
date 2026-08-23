#!/usr/bin/env python3
"""microwalk adapter: Microwalk differential address-trace analysis over Intel Pin.

Microwalk traces the memory-access and control-flow of a target under Pin across
many secret inputs and reports where the trace depends on the secret. It is the
maintained successor to DATA, and the right lens for the address-data class where
a timing test sees nothing and a taint tool cannot separate the fix from the bug.

A pair ships a microwalk target implementing the framework's wrapper protocol
(RunTarget/InitTarget over a stdin testcase pipe, with the PinNotify* markers the
pintool hooks by name). The wrapper is built with the target, its .map file is
generated, testcases are synthesised, and the pipeline (trace, preprocess,
control-flow-leakage) runs. A leak that localises into the traced target region is
a detection; zero leakages is clean; a Pin or pipeline failure is INCONCLUSIVE
(blocked), never a silent zero, exactly as PR-1 fixes it.

Build happens in the target's build image (the microwalk image for pure C, the
openssl cell for OpenSSL targets, which link libcrypto statically); the trace and
analysis always run in the microwalk image. -Wl,-z,now removes the lazy-binding
first-testcase artifact so the leakage count is the count of secret-dependent
sites in the traced code.
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
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[4]
MW_IMAGE = ("ghcr.io/microwalk-project/microwalk@sha256:"
            "4c516c906c96ea76e68ac97ddd8ce41477c42547606351920fb8011c824cbcd2")
ADAPTERS = REPO / "src" / "corpus" / "score" / "adapters"
PINTOOL = "/mw/pintool/obj-intel64/PinTracer.so"
PIN = "/mw/pin/pin"


def _testcases(mode: str, n: int, length: int) -> list[bytes]:
    """Synthesise n testcases of `length` bytes, deterministically.

    random: a spread of distinct byte patterns, enough to make a secret-indexed
      access vary its address across inputs.
    prefix: input j shares a j-byte prefix with the 0xAA candidate the tag target
      compares against, so the early-exit loop runs a secret-dependent number of
      times. This exercises a branch leak that random inputs would almost never
      trigger, so a missed branch is the tool's, not the input distribution's.
    """
    out = []
    if mode == "prefix":
        for j in range(min(n, length + 1)):
            out.append(bytes([0xAA] * j + [0x55] * (length - j)))
    else:
        for j in range(n):
            out.append(bytes([(j * 31 + k * 17 + 1) & 0xFF for k in range(length)]))
    return out


def _config(work: str, target_name: str) -> str:
    return f"""general:
  logger:
    log-level: warning
  monitor:
    enable: false

testcase:
  module: load
  module-options:
    input-directory: {work}/testcases

trace:
  module: pin
  module-options:
    output-directory: {work}/work/traces
    pin-tool-path: {PINTOOL}
    pin-path: {PIN}
    wrapper-path: {work}/{target_name}
    images:
      - {target_name}
  options:
    input-buffer-size: 4

preprocess:
  module: pin
  module-options:
    output-directory: {work}/work/traces
    store-traces: true
    keep-raw-traces: false
  options:
    input-buffer-size: 2
    max-parallel-threads: 4

analysis:
  modules:
    - module: control-flow-leakage
      module-options:
        output-directory: {work}/persist/results
        map-files:
          - {work}/{target_name}.map
        dump-call-tree: false
  options:
    input-buffer-size: 1
    max-parallel-threads: 1
"""


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 900) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "microwalk.toml").read_text())
    target, header = cfg["target"], cfg.get("header")
    opt = opt or cfg.get("opt", "O2")
    build_image = cfg.get("build_image", MW_IMAGE)
    libs = cfg.get("libs", "")
    static = " -static" if cfg.get("static") else ""
    extra = " ".join(f"/work/{s}" for s in cfg.get("extra_sources", []))
    length = int(cfg.get("input_len", 16))
    n = int(cfg.get("n_testcases", 16))
    mode = cfg.get("testcase_mode", "random")
    target_func = cfg.get("target_func")
    host = {"kernel": platform.release(), "machine": platform.machine()}

    import tempfile
    with tempfile.TemporaryDirectory(prefix="microwalk-") as td:
        work = pathlib.Path(td)
        (work / "testcases").mkdir()
        (work / "work" / "traces").mkdir(parents=True)
        (work / "persist" / "results").mkdir(parents=True)
        # Sources into the work dir so one mount serves build, trace and analyse.
        shutil.copy(ADAPTERS / "microwalk_main.c", work / "microwalk_main.c")
        shutil.copy(ADAPTERS / target, work / target)
        shutil.copy(src / f"{arm}.c", work / f"{arm}.c")
        if header:
            hp = src / header
            if not hp.exists():
                hp = harness / header
            shutil.copy(hp, work / header)
        for s in cfg.get("extra_sources", []):
            shutil.copy(src / s, work / s)
        for i, tc in enumerate(_testcases(mode, n, length)):
            (work / "testcases" / f"t{i}.testcase").write_bytes(tc)
        (work / "config.yml").write_text(_config("/work", "target"), encoding="utf-8")

        build = subprocess.run(
            ["podman", "run", "--rm", "--network=none", "--user", "0",
             "-v", f"{work}:/work:rw,Z", "--entrypoint", "sh", build_image, "-c",
             f"cd /work && gcc -{opt} -g -fno-inline -fno-split-stack -no-pie "
             f"-Wl,-z,now{static} -I/work -o /work/target "
             f"/work/microwalk_main.c /work/{target} /work/{arm}.c {extra} {libs} "
             f"2>/work/cc.err || {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}"],
            capture_output=True, text=True, timeout=timeout)
        if "BUILD_FAILED" in build.stdout or build.returncode == 3:
            return {"adapter": "microwalk", "tool": "microwalk", "arm": arm,
                    "status": "error", "detail": "target build failed",
                    "cc_err": build.stdout[-800:], "host": host}

        run = subprocess.run(
            ["podman", "run", "--rm", "--network=none", "--user", "0",
             "-v", f"{work}:/work:rw,Z", "--entrypoint", "sh", MW_IMAGE, "-c",
             "cd /work && dotnet /mw/mapfilegenerator/MapFileGenerator.dll "
             "/work/target /work/target.map >/dev/null 2>&1; "
             "cd /mw/microwalk && dotnet Microwalk.dll /work/config.yml 2>&1"],
            capture_output=True, text=True, timeout=timeout)
        out = run.stdout
        cs = work / "persist" / "results" / "call-stacks.txt"
        sites = re.findall(r"\[L\] (\S+) \((memory access|jump|return|call)\)",
                           cs.read_text()) if cs.exists() else []

    m = re.search(r"Total number of leakages:\s*(\d+)", out)
    if m is None:
        # Pin could not instrument, or the pipeline errored. INCONCLUSIVE, not zero.
        return {"adapter": "microwalk", "tool": "microwalk", "arm": arm,
                "status": "budget_exhausted",
                "detail": "microwalk produced no leakage count (pin/pipeline error)",
                "tail": out[-600:], "host": host}
    if target_func:
        sites = [s for s in sites if target_func in s[0]]
        count = len(sites)
    else:
        count = int(m.group(1))
    status = "leak_reported" if count > 0 else "clean"
    return {"adapter": "microwalk", "tool": "microwalk", "arm": arm,
            "status": status,
            "detail": f"{count} secret-dependent site(s) in the traced target",
            "leaking_sites": [{"at": a, "kind": k} for a, k in sites][:10],
            "total_leakages": int(m.group(1)), "host": host}


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
