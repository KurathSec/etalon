#!/usr/bin/env python3
"""Build every pair in every declared cell, and record what the compiler emitted.

This is where the project's central design claim becomes a measurement rather
than an assertion. A pair pins vendor, version, optimisation level and target
triple, and ground truth is keyed to the resulting binary, because the same
source does not necessarily emit the same defect under a different build.

Two things are recorded per (pair, arm, cell):

  sha256_text  the digest of the .text section, which is what BIN-1 rebuilds
               against. Not the whole file, and not the container image: podman
               build is not bit-reproducible, and a control that is always red
               is not a control.

  leak_sites   the count of instructions from the pair's declared
               instruction_class inside the entry symbol. BIN-2 requires the
               vulnerable arm to emit STRICTLY MORE of them than the patched
               arm, which is the mechanical evidence that the patch removed the
               defect IN THIS CELL. A cell where that difference disappears is
               not a failure of the corpus; it is the finding that the defect is
               not emitted there, and it is the reason a source-only benchmark
               measures the compiler rather than the checker.

               Stated honestly, this is a PROXY. The exact check localises to
               the declared source lines through DWARF, and counting over the
               whole entry symbol also counts the loop back-edge, which is why
               the patched arm's count is legitimately non-zero. The proxy is
               sound for the comparison it makes and would not be sound as an
               absolute statement about either arm alone.

Usage: bin/build.py [--pair NAME] [--jobs N]
Exit codes: 0 built and recorded, 1 a build failed, 2 could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CELLS = {
    "gcc-12.2.0-O0-x86_64-linux-gnu": ("localhost/ct-toolchain/gcc-bookworm:1", "O0"),
    "gcc-12.2.0-O2-x86_64-linux-gnu": ("localhost/ct-toolchain/gcc-bookworm:1", "O2"),
    "gcc-12.2.0-O3-x86_64-linux-gnu": ("localhost/ct-toolchain/gcc-bookworm:1", "O3"),
    "gcc-12.2.0-Os-x86_64-linux-gnu": ("localhost/ct-toolchain/gcc-bookworm:1", "Os"),
    "clang-14.0.6-O0-x86_64-linux-gnu": ("localhost/ct-toolchain/clang-bookworm:1", "O0"),
    "clang-14.0.6-O2-x86_64-linux-gnu": ("localhost/ct-toolchain/clang-bookworm:1", "O2"),
    "clang-14.0.6-O3-x86_64-linux-gnu": ("localhost/ct-toolchain/clang-bookworm:1", "O3"),
    "clang-14.0.6-Os-x86_64-linux-gnu": ("localhost/ct-toolchain/clang-bookworm:1", "Os"),
}


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(" ".join(cmd) + "\n" + r.stderr)
    return r.stdout


def probe(image: str, outdir: Path, binary: str, symbol: str,
          classes: list[str]) -> dict:
    """Read back what the compiler actually emitted for one entry symbol."""
    text = run(["podman", "run", "--rm", "--network=none",
                "-v", f"{outdir}:/out:ro,Z", image, "sh", "-c",
                f"objdump -d --disassemble='{symbol}' /out/{binary}"])
    body = [l for l in text.splitlines() if "\t" in l]
    mnemonics = []
    for line in body:
        parts = line.split("\t")
        if len(parts) >= 3:
            mnemonics.append(parts[2].split()[0] if parts[2].split() else "")
    # An undeclared instruction class yields NA, never 0. A pair with no
    # declared class has not been measured as having no leak instructions; it
    # has not been measured at all, and printing 0 there is the defect this
    # programme keeps rediscovering, a default presented as a measurement.
    hits = sum(1 for m in mnemonics if m in classes) if classes else None
    sec = run(["podman", "run", "--rm", "--network=none",
               "-v", f"{outdir}:/out:ro,Z", image, "sh", "-c",
               f"objcopy -O binary --only-section=.text /out/{binary} /tmp/t "
               f"&& sha256sum /tmp/t"]).split()[0]
    return {"instructions_in_symbol": len(mnemonics),
            "leak_class_instructions": hits,
            "sha256_text": sec,
            "textprint": "\n".join(body[:400])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair")
    ap.add_argument("--check", action="store_true",
                    help="BIN-1: rebuild and compare against the committed lock "
                         "instead of writing it")
    args = ap.parse_args()

    pairs = sorted(p.parent for p in (REPO / "pairs").glob("*/pair.toml"))
    if args.pair:
        pairs = [p for p in pairs if p.name == args.pair]
    if not pairs:
        print("build: no pairs", file=sys.stderr)
        return 2

    lock, failures = {}, []
    for pair in pairs:
        man = tomllib.loads((pair / "pair.toml").read_text())
        # build.py only handles pairs whose declared cells are gcc/clang
        # instruction-level cells it knows. Pairs that declare no cells, or that
        # declare a different toolchain cell (the OpenSSL-linked ecdsa pairs,
        # scored on recorded traces), are not built here.
        req = man.get("toolchain", {}).get("cells_required") or []
        if not any(c in CELLS for c in req):
            continue
        symbol = man["build"][0]["entry_symbol"]
        sites = man.get("site") or []
        classes = sites[0].get("instruction_class", []) if sites else []
        for cell, (image, opt) in CELLS.items():
            out = REPO / "cache" / "build" / pair.name / cell
            out.mkdir(parents=True, exist_ok=True)
            for arm in ("vulnerable", "patched"):
                try:
                    run(["podman", "run", "--rm", "--network=none",
                         "-v", f"{pair}/src:/src:ro,Z", "-v", f"{out}:/out:rw,Z",
                         "-e", "SOURCE_DATE_EPOCH=1700000000",
                         image, "/src/build.sh", arm, opt, "/out"])
                    info = probe(image, out, f"harness_{arm}", symbol, classes)
                except RuntimeError as exc:
                    failures.append(f"{pair.name}/{cell}/{arm}: {exc}")
                    continue
                tp = REPO / "locks" / "textprints" / pair.name / cell
                tp.mkdir(parents=True, exist_ok=True)
                (tp / f"{arm}.asm").write_text(info.pop("textprint"), encoding="utf-8")
                lock.setdefault(pair.name, {}).setdefault(cell, {})[arm] = info
            v = lock[pair.name][cell]['vulnerable']['leak_class_instructions']
            q = lock[pair.name][cell]['patched']['leak_class_instructions']
            fmt = lambda x: " NA" if x is None else f"{x:>3}"
            verdict = ("no declared class" if v is None
                       else "leak emitted" if v > q else "LEAK NOT EMITTED")
            print(f"  {pair.name:<20} {cell:<32} "
                  f"vuln={fmt(v)} patch={fmt(q)}  {verdict}")

    lock_path = REPO / "locks" / "binaries.lock.json"
    if args.check:
        if not lock_path.exists():
            print("build: no committed lock to check against", file=sys.stderr)
            return 2
        committed = json.loads(lock_path.read_text())
        drift = []
        # Only compare pairs actually rebuilt this run. A pair absent from the
        # fresh build (because it declares no cells) is not drift.
        for pair_name, cells in lock.items():
            for cell, arms in cells.items():
                for arm, info in arms.items():
                    was = committed.get(pair_name, {}).get(cell, {}).get(arm)
                    if was is None:
                        drift.append(f"{pair_name}/{cell}/{arm}: absent from the lock")
                    elif was["sha256_text"] != info["sha256_text"]:
                        drift.append(f"{pair_name}/{cell}/{arm}: .text digest moved")
        if drift:
            print(f"\nBIN-1 FAIL: {len(drift)} discrepancy(ies)", file=sys.stderr)
            for d in drift:
                print("  " + d, file=sys.stderr)
            return 1
        n = sum(len(a) for c in lock.values() for a in c.values())
        print(f"\nBIN-1 PASS: {n} binaries rebuilt to their recorded .text digest")
        return 0

    lock_path.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nbuild: recorded {sum(len(c) for c in lock.values())} cell(s) "
          f"across {len(lock)} pair(s)")
    for f in failures:
        print("  FAILED " + f, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
