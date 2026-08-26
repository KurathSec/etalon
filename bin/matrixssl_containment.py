#!/usr/bin/env python3
"""Resolve the containment question by timing the regions together, and record it.

The paper reported three figures for this case that cannot all be what their names
say: an isolated scalar-multiplication call, a whole signature that must contain
one, and a retired-instruction count. The signature came out cheaper than the call,
which is impossible for the same quantity, and which of the three was wrong was
left undetermined because each came from a different harness on a different run.

Running them in one process settles it, and the answer is that the isolated-call
figure was ours. The argument the harness passed as scratch is not scratch: it is
the curve's `a` coefficient, forwarded to eccProjectiveDblPoint. secp256r1 is
flagged isOptimized in ecc_curve_data.c ("1 if optimized with field parameter
A=-3"), so ecc_keygen.c never allocates it and the deployed call passes NULL, which
selects the fast doubling. Passing a non-NULL zero selects the generic path for a
different curve, at 3.46x the cost of the deployed call and 3.42x the
library's own key generation, which is the ratio this script records.

Usage: matrixssl_containment.py <work-dir-from-matrixssl_rebuild> [repeats]
"""
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "matrixssl_containment.json"
ROW = re.compile(r"^(\w+)\s+n=(\d+)\s+min=(\d+)\s+p10=(\d+)\s+median=(\d+)\s+"
                 r"mean=(\d+)\s+max=(\d+)")
VERSION = "4-3-0"


def run(work: pathlib.Path, core: str) -> dict:
    m = f"matrixssl-{VERSION}-open"
    out = work / "dumps"
    subprocess.run(
        ["podman", "run", "--rm", "--network=none",
         "-v", f"{work}/build:/w:Z",
         "-v", f"{REPO}/pairs/matrixssl-minerva/acquire:/a:ro,Z",
         "-v", f"{out}:/out:Z", "localhost/ct-toolchain/gcc-bookworm:1", "sh", "-c",
         f"cd /w && gcc -O2 -DNREP=1500 -I{m} -I{m}/crypto -I{m}/core/include "
         f"-I{m}/core/osdep/include -I{m}/core -o /out/containment /a/containment.c "
         f"{m}/crypto/libcrypt_s.a {m}/core/libcore_s.a -lm"],
        check=True, capture_output=True, text=True)
    r = subprocess.run(
        ["podman", "run", "--rm", "--network=none", "-v", f"{out}:/out:Z",
         "localhost/ct-toolchain/gcc-bookworm:1", "sh", "-c",
         f"taskset -c {core} /out/containment"],
        check=True, capture_output=True, text=True)
    rows = {}
    for line in r.stdout.splitlines():
        mm = ROW.match(line.strip())
        if mm:
            rows[mm.group(1)] = {"n": int(mm.group(2)), "min": int(mm.group(3)),
                                 "p10": int(mm.group(4)), "median": int(mm.group(5)),
                                 "mean": int(mm.group(6)), "max": int(mm.group(7))}
    if set(rows) != {"sign", "mulmod", "mulbare", "mulnull", "genkey"}:
        sys.exit(f"containment: unexpected regions {sorted(rows)}")
    return rows


def main() -> int:
    work = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "")
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    if not (work / "build").is_dir():
        sys.exit("usage: matrixssl_containment.py <work-dir> [repeats]")
    runs = [run(work, "3") for _ in range(reps)]

    med = {k: sorted(r[k]["median"] for r in runs)[len(runs) // 2] for k in runs[0]}
    # The two numbers that must agree if the diagnosis is right: eccMulmod called the
    # way the LIBRARY calls it, and the library's own key generation, which is where
    # psEccDsaSignCommon gets its scalar multiplication.
    agree = abs(med["mulnull"] - med["genkey"]) / med["genkey"]
    doc = {
        "finding": ("the isolated-call figure was the outlier, and the cause was the "
                    "harness passing a curve parameter where the library passes NULL"),
        "why": __doc__.strip().split("\n\n")[1],
        "reading": (
            "mulnull and genkey agree to within about one per cent, so eccMulmod "
            "called with the library's own argument IS the deployed call. sign exceeds "
            "genkey by the hashing, inversion and encoding a signature adds. mulmod, "
            "the region the earlier harness timed, is several times either, because a "
            "non-NULL zero selects the generic doubling for a=0 instead of the "
            "optimised a=-3 path. Nothing here is a property of MatrixSSL; it is a "
            "property of how this corpus called it."),
        "generator": "bin/matrixssl_containment.py",
        "version": VERSION,
        "repeats": reps,
        "median_ticks": med,
        "mulnull_vs_genkey_relative_gap": agree,
        "harness_overstatement_factor": med["mulmod"] / med["genkey"],
        "runs": runs,
    }
    if agree > 0.02:
        sys.exit(f"containment: mulnull and genkey differ by {agree:.1%}, which does "
                 f"not support the diagnosis; not writing a result that is not there")
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"containment: genkey {med['genkey']:,} vs mulnull {med['mulnull']:,} ticks "
          f"({agree:.2%} apart); the earlier harness's region was "
          f"{med['mulmod'] / med['mulnull']:.2f}x the deployed call "
          f"({doc['harness_overstatement_factor']:.2f}x the library's own key generation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
