#!/usr/bin/env python3
"""Retired instructions per nonce class, differenced to remove startup.

Two things this settles.

First, containment. The earlier count was 42,633,192 instructions for a call the
paper measured at 5,535,140 ticks, and neither figure was what its name said: both
came from a driver passing a curve parameter where the library passes NULL, so both
described scalar multiplication on a different curve. Corrected, the call retires
about nine and a half million instructions in about 1.6 million ticks, a rate a wide
out-of-order core reaches. The impossible arithmetic is gone.

Second, and more useful, the count and the clock disagree about the SHAPE of the
residual, and that disagreement is the paper's practitioner claim made quantitative.
One leading zero and sixty-three leading zeros retire almost exactly the same number
of instructions, because that is what the fix's dummy operations are for. They do not
take the same time. The work is balanced; the cost is not.

Callgrind counts include process startup, so each class is run at two call counts and
differenced: the slope is the per-call figure and the intercept is discarded.
"""
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "matrixssl_icount.json"
IMG = "localhost/ct-toolchain/varlat:1"
VERSION = "4-3-0"
BITS = [256, 255, 193, 192]
LOW, HIGH = 100, 200
REFS = re.compile(r"I\s+refs:\s+([\d,]+)")


def count(work: pathlib.Path, bits: int, calls: int) -> int:
    r = subprocess.run(
        ["podman", "run", "--rm", "--network=none", "-v", f"{work}/ic:/ic:Z", IMG, "sh", "-c",
         f"valgrind --tool=callgrind --callgrind-out-file=/dev/null /ic/icount {bits} {calls}"],
        check=True, capture_output=True, text=True)
    m = REFS.search(r.stderr) or REFS.search(r.stdout)
    if not m:
        sys.exit(f"icount: no instruction count for {bits} bits at {calls} calls")
    return int(m.group(1).replace(",", ""))


def main() -> int:
    work = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "")
    m = f"matrixssl-{VERSION}-open"
    if not (work / "build" / m).is_dir():
        sys.exit("usage: matrixssl_icount.py <work-dir-from-matrixssl_rebuild>")
    (work / "ic").mkdir(exist_ok=True)
    subprocess.run(
        ["podman", "run", "--rm", "--network=none", "-v", f"{work}/build:/w:Z",
         "-v", f"{REPO}/pairs/matrixssl-minerva/acquire:/a:ro,Z",
         "-v", f"{work}/ic:/ic:Z", IMG, "sh", "-c",
         f"cd /w && gcc -O2 -I{m} -I{m}/crypto -I{m}/core/include -I{m}/core/osdep/include "
         f"-I{m}/core -o /ic/icount /a/icount.c {m}/crypto/libcrypt_s.a "
         f"{m}/core/libcore_s.a -lm"], check=True, capture_output=True, text=True)

    per = {}
    for b in BITS:
        lo, hi = count(work, b, LOW), count(work, b, HIGH)
        per[b] = (hi - lo) / (HIGH - LOW)
    base = per[256]
    rows = {str(b): {"instructions_per_call": per[b],
                     "delta_vs_256": base - per[b],
                     "percent_vs_256": (base - per[b]) / base * 100,
                     "leading_zeros": 256 - b if b > 192 else 64,
                     "digits": 4 if b > 192 else 3} for b in BITS}

    cont = json.loads((REPO / "results" / "matrixssl_containment.json").read_text())
    ticks = cont["median_ticks"]["mulnull"]
    doc = {
        "finding": ("the fix balances the instruction count across leading zeros and does "
                    "not balance the cost"),
        "why": __doc__.strip().split("\n\n")[2],
        "reading": (
            "One leading zero and sixty-three each SAVE almost the same number of "
            "instructions, while the measured time differs by nearly two orders of "
            "magnitude, which is why an instruction count cannot stand in for the cost "
            "here. delta_vs_256 is the 256-bit count minus the shorter class's, so a "
            "positive delta is a saving; an earlier revision of this field read it as an "
            "addition and the paper repeated the inverted sign."),
        "generator": "bin/matrixssl_icount.py",
        "version": VERSION,
        "method": (f"callgrind at {LOW} and {HIGH} calls per class, differenced, so process "
                   f"startup cancels; one nonce class per run with the scalar fixed"),
        "per_call": rows,
        "instructions_per_tick": base / ticks,
        "tick_reference": "results/matrixssl_containment.json median_ticks.mulnull",
    }
    if doc["instructions_per_tick"] > 12:
        sys.exit(f"icount: {doc['instructions_per_tick']:.1f} instructions per tick is not "
                 f"a rate any core reaches; the two figures still do not describe one call")
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"icount: {base:,.0f} instructions per call over {ticks:,} ticks "
          f"({doc['instructions_per_tick']:.2f} per tick); one leading zero costs "
          f"{rows['255']['delta_vs_256']:,.0f} and sixty-three cost "
          f"{rows['193']['delta_vs_256']:,.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
