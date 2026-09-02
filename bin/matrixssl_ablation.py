#!/usr/bin/env python3
"""The MatrixSSL mechanism ablation: build the two candidate terms out, one at a time, and measure.

WHY THIS EXISTS
The fixed eccMulmodCt converts each leading-zero iteration from the real ladder
step to a dummy step that is matched in operation count and not in cost, and the
paper named two candidate terms for the cost gap: the dummy double writes to a
scratch point, so eccProjectiveDblPoint performs three pstm_copy calls the
in-place real double skips; and the dummy operands are the fixed pair (P, 2P)
rather than the evolving ladder state, which feeds magnitude-sensitive
arithmetic the same values every iteration. Which term dominates was a
statement about the code. This script turns it into a measurement by building
each term out and timing the result under the same designs as the site figures.

WHAT IT BUILDS
Five builds of the first fixed release from one verified source tree, differing
only inside eccMulmodCt's two dummy blocks. orig: the shipped code, rebuilt in
the same session as a same-day baseline. nop: the dummy blocks do nothing, so a
leading-zero iteration costs nothing and the difference measures a full real
step. inplace: the dummy double is made in place on the scratch point, which
removes the three copies and keeps the fixed operands. evolvingoop: the dummy
step runs on a scratch pair that evolves like the real ladder, with the double
still out of place, which removes the fixed operands and keeps the copies.
evolving: both removed, the real step replicated on the scratch pair. Each is
acquired with the site harness under every design the site figures use, the
same repeats, batches and measurements, pinned to the same core, and the
committed first-release dumps stand beside the same-day baseline.

THE ACCOUNTING
For a design that varies the leading-zero count alone, the class difference
divided by the number of converted iterations is the per-iteration cost gap
between a real step and a dummy step. The copy term is the per-iteration
difference between inplace and orig; the operand term is the difference between
evolvingoop and orig; evolving carries what neither term explains. The nop
build supplies the denominator: a whole real step in ticks. samedigit converts
sixty-three iterations and is the precise lever; bit255 converts one and is the
check. same converts none and is the null; diffdigit changes the digit count
and so the loop bound, and is reported but enters no per-iteration figure.

THE READING
A real ladder step costs about 3,800 ticks on this host, and the shipped dummy
step recovers all but about 1,130 of it, so one leading zero saves about thirty
per cent of a step. The two terms are far from equal. Making the dummy double in
place moves the gap by about twenty ticks: the three copies are nearly free.
Letting the dummy operands evolve as the real ladder's do removes about 1,080
ticks of the 1,130: the fixed operands account for the gap, and the two terms
add within noise. With both changed, about eighty ticks per converted iteration
remain over sixty-three iterations and about 690 over one, so the remainder is
small and does not scale with the count alone; it is reported, not attributed.
The same-day rebuild of the shipped code reproduces the committed first-release
figures within their spread, so the variants are comparable to either. What the
fix balanced was the operation count; what it left unbalanced was the
arithmetic's dependence on the operand values, which a dummy step on constant
operands does not hide.

ASSUMPTIONS
the shipped dummy step and the real step differ only in what the ablation changes: which point is doubled, whether in place, and whether the operands evolve
the site estimator (95th-percentile crop, seeded bootstrap) applies unchanged, so the figures are comparable to the site figures
the per-iteration figure divides by the converted-iteration count the design fixes (one for bit255, sixty-three for samedigit)
a same-day orig build that agrees with the committed dumps within their intervals licenses comparing the variants to either
timing figures are in TSC ticks on the acquisition host and are host-conditional like every timing figure here

Usage: matrixssl_ablation.py --patch VARIANT SRC DST
       matrixssl_ablation.py --import WORKDIR
       matrixssl_ablation.py [--write] [--check]
"""
from __future__ import annotations
import argparse
import difflib
import gzip
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
RAW = REPO / "results" / "raw" / "matrixssl" / "ablation"
BASELINE = REPO / "results" / "raw" / "matrixssl" / "repeats"
OUT = REPO / "results" / "matrixssl_ablation.json"
MANIFEST = RAW / "manifest.json"
VARIANTS = ("orig", "nop", "inplace", "evolvingoop", "evolving")
DESIGNS = ("same", "bit255", "samedigit", "diffdigit")
# Converted iterations per design: how many loop iterations the shorter class turns
# from the real step into the dummy step. diffdigit changes the digit count, so its
# classes run different loop bounds and it carries no per-iteration figure.
CONVERTED = {"same": 0, "bit255": 1, "samedigit": 63, "diffdigit": None}
NAME = re.compile(r"^(?P<variant>[a-z]+)\.(?P<design>[a-z0-9]+)\.r(?P<rep>\d+)\.bin(?:\.gz)?$")

ADD_DUMMY = ("err = eccProjectiveAddPoint(pool,\n"
             "                    M[0], M[1], M[2],\n"
             "                    modulus, &mp, tmp_int);")
DBL_DUMMY = ("err = eccProjectiveDblPoint(pool,\n"
             "                    M[1], M[2],\n"
             "                    modulus, &mp, tmp_int);")
INIT_ANCHOR = ("err = eccProjectiveDblPoint(pool, tG, M[1], modulus, &mp, tmp_int);\n"
               "    if (err != PS_SUCCESS)\n"
               "    {\n"
               "        goto done;\n"
               "    }\n")
SCRATCH_INIT = INIT_ANCHOR + """
    /* ablation: a scratch pair (M[3], M[4]) that starts as (M[0], M[1]) and
       evolves under the dummy step exactly as the real ladder would. */
    if ((err = pstm_copy(&M[0]->x, &M[3]->x)) != PS_SUCCESS) { goto done; }
    if ((err = pstm_copy(&M[0]->y, &M[3]->y)) != PS_SUCCESS) { goto done; }
    if ((err = pstm_copy(&M[0]->z, &M[3]->z)) != PS_SUCCESS) { goto done; }
    if ((err = pstm_copy(&M[1]->x, &M[4]->x)) != PS_SUCCESS) { goto done; }
    if ((err = pstm_copy(&M[1]->y, &M[4]->y)) != PS_SUCCESS) { goto done; }
    if ((err = pstm_copy(&M[1]->z, &M[4]->z)) != PS_SUCCESS) { goto done; }
"""
NOP_BLOCK = ("/* ablation: no dummy operations */\n"
             "            err = PS_SUCCESS;\n"
             "            if (err != PS_SUCCESS)\n"
             "            {\n"
             "                goto done;\n"
             "            }")
DUMMY_BLOCK = (ADD_DUMMY + "\n"
               "            if (err != PS_SUCCESS)\n"
               "            {\n"
               "                goto done;\n"
               "            }\n"
               "            " + DBL_DUMMY)


def _count(text: str, needle: str, want: int, what: str) -> None:
    n = text.count(needle)
    if n != want:
        sys.exit(f"matrixssl_ablation: expected {want} of {what}, found {n}; "
                 "the source tree is not the one this patch was written against")


def _scratch(fn: str) -> str:
    """Allocate two more points and seed them from (M[0], M[1])."""
    _count(fn, "psEccPoint_t *tG, *M[3];", 1, "the M[3] declaration")
    _count(fn, "for (i = 0; i < 3; i++)", 2, "the M[] alloc/free loops")
    _count(fn, INIT_ANCHOR, 1, "the M[1] = 2G anchor")
    fn = fn.replace("psEccPoint_t *tG, *M[3];", "psEccPoint_t *tG, *M[5];")
    fn = fn.replace("for (i = 0; i < 3; i++)", "for (i = 0; i < 5; i++)")
    return fn.replace(INIT_ANCHOR, SCRATCH_INIT)


def patch_orig(fn: str) -> str:
    return fn


def patch_nop(fn: str) -> str:
    _count(fn, DUMMY_BLOCK, 2, "the dummy block")
    return fn.replace(DUMMY_BLOCK, NOP_BLOCK)


def patch_inplace(fn: str) -> str:
    _count(fn, DBL_DUMMY, 2, "the dummy double")
    return fn.replace(DBL_DUMMY, DBL_DUMMY.replace("M[1], M[2],", "M[2], M[2],"))


def patch_evolvingoop(fn: str) -> str:
    _count(fn, ADD_DUMMY, 2, "the dummy add")
    _count(fn, DBL_DUMMY, 2, "the dummy double")
    _count(fn, "continue;", 2, "the dummy continue")
    fn = _scratch(fn)
    fn = fn.replace(ADD_DUMMY, ADD_DUMMY.replace("M[0], M[1], M[2],", "M[3], M[4], M[4],"))
    fn = fn.replace(DBL_DUMMY, DBL_DUMMY.replace("M[1], M[2],", "M[3], M[2],"))
    swap = ("{ psEccPoint_t *swp = M[3]; M[3] = M[2]; M[2] = swp; } /* ablation */\n"
            "            continue;")
    return fn.replace("continue;", swap)


def patch_evolving(fn: str) -> str:
    _count(fn, ADD_DUMMY, 2, "the dummy add")
    _count(fn, DBL_DUMMY, 2, "the dummy double")
    fn = _scratch(fn)
    fn = fn.replace(ADD_DUMMY, ADD_DUMMY.replace("M[0], M[1], M[2],", "M[3], M[4], M[4],"))
    return fn.replace(DBL_DUMMY, DBL_DUMMY.replace("M[1], M[2],", "M[3], M[3],"))


PATCHES = {"orig": patch_orig, "nop": patch_nop, "inplace": patch_inplace,
           "evolvingoop": patch_evolvingoop, "evolving": patch_evolving}


def patch(variant: str, src: pathlib.Path, dst: pathlib.Path) -> None:
    text = src.read_text()
    start = text.index("int32_t eccMulmodCt(")
    end = text.index("# endif /* USE_CONSTANT_TIME_ECC_MULMOD */", start)
    fn = text[start:end]
    new = PATCHES[variant](fn)
    if variant != "orig" and new == fn:
        sys.exit(f"matrixssl_ablation: {variant} changed nothing")
    dst.write_text(text[:start] + new + text[end:])
    print(f"matrixssl_ablation: {variant} written to {dst} "
          f"({sum(1 for _ in difflib.unified_diff(fn.splitlines(), new.splitlines(), lineterm=''))} diff lines)")


def _report_module():
    spec = importlib.util.spec_from_file_location("matrixssl_report", REPO / "bin" / "matrixssl_report.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def do_import(work: pathlib.Path) -> None:
    """Copy a work directory's dumps into the committed raw tree, gzipped, with digests."""
    RAW.mkdir(parents=True, exist_ok=True)
    dumps = sorted((work / "ablation" / "dumps").glob("*.bin"))
    if not dumps:
        sys.exit(f"matrixssl_ablation: no dumps under {work}/ablation/dumps")
    files = {}
    for d in dumps:
        m = NAME.match(d.name)
        if not m or m["variant"] not in VARIANTS or m["design"] not in DESIGNS:
            sys.exit(f"matrixssl_ablation: unexpected dump name {d.name}")
        gz = RAW / (d.name + ".gz")
        with open(d, "rb") as fi, gzip.GzipFile(gz, "wb", mtime=0) as fo:
            shutil.copyfileobj(fi, fo)
        files[d.name] = hashlib.sha256(d.read_bytes()).hexdigest()
    digests = (work / "ablation" / "digests.txt").read_text() if (work / "ablation" / "digests.txt").exists() else ""
    orig = work / "build" / "matrixssl-4-3-0-open" / "crypto" / "pubkey" / "ecc_math.c"
    diffs = {}
    for v in VARIANTS:
        pv = work / "ablation" / "build" / f"mx-{v}" / "crypto" / "pubkey" / "ecc_math.c"
        if pv.exists() and orig.exists():
            diffs[v] = "\n".join(difflib.unified_diff(
                orig.read_text().splitlines(), pv.read_text().splitlines(),
                "matrixssl-4-3-0-open/crypto/pubkey/ecc_math.c", f"mx-{v}/crypto/pubkey/ecc_math.c",
                lineterm="", n=2))
    MANIFEST.write_text(json.dumps({
        "what": "raw dudect dumps of the mechanism ablation builds, one per (variant, design, repeat); "
                "9 bytes per record, class then int64 ticks, as results/raw/matrixssl/repeats",
        "generator": "bin/matrixssl_ablation.py --import <work-dir>",
        "dump_sha256": files, "build_digests": digests, "source_diffs": diffs,
    }, indent=2) + "\n")
    print(f"matrixssl_ablation: imported {len(files)} dumps, manifest with {len(diffs)} diffs")


def build() -> dict:
    rep = _report_module()
    runs = []
    for f in sorted(RAW.glob("*.bin.gz")):
        m = NAME.match(f.name)
        cl, t = rep.load(f)
        d, lo, hi, n = rep.stats(cl, t)
        runs.append({"file": str(f.relative_to(REPO)), "variant": m["variant"], "design": m["design"],
                     "repeat": int(m["rep"]), "delta_ticks": d, "ci95": [lo, hi],
                     "records": int(cl.size), "cropped_sample_size": n})
    for f in sorted(BASELINE.glob("4-3-0.*.bin.gz")):
        m = rep.NAME.match(f.name)
        cl, t = rep.load(f)
        d, lo, hi, n = rep.stats(cl, t)
        runs.append({"file": str(f.relative_to(REPO)), "variant": "committed", "design": m["design"],
                     "repeat": int(m["rep"]), "delta_ticks": d, "ci95": [lo, hi],
                     "records": int(cl.size), "cropped_sample_size": n})
    if not any(r["variant"] != "committed" for r in runs):
        sys.exit(f"matrixssl_ablation: no ablation dumps under {RAW.relative_to(REPO)}")
    summary = {}
    for v in ("committed",) + VARIANTS:
        for dsg in DESIGNS:
            ds = [r["delta_ticks"] for r in runs if r["variant"] == v and r["design"] == dsg]
            if not ds:
                continue
            k = CONVERTED[dsg]
            summary.setdefault(v, {})[dsg] = {
                "repeats": len(ds), "mean_delta_ticks": sum(ds) / len(ds),
                "min_delta_ticks": min(ds), "max_delta_ticks": max(ds),
                "per_iteration_ticks": (sum(ds) / len(ds) / k) if k else None,
                "converted_iterations": k,
            }
    attribution = {}
    for dsg in ("samedigit", "bit255"):
        per = {v: summary.get(v, {}).get(dsg, {}).get("per_iteration_ticks") for v in VARIANTS}
        if any(per[v] is None for v in VARIANTS):
            continue
        attribution[dsg] = {
            "real_step_ticks": per["nop"],
            "shipped_gap_ticks": per["orig"],
            "shipped_gap_fraction_of_step": per["orig"] / per["nop"] if per["nop"] else None,
            "copy_term_ticks": per["inplace"] - per["orig"],
            "operand_term_ticks": per["evolvingoop"] - per["orig"],
            "both_removed_gap_ticks": per["evolving"],
            "unexplained_fraction_of_shipped_gap": per["evolving"] / per["orig"] if per["orig"] else None,
        }
    doc = __doc__
    return {
        "finding": FINDING,
        "why": doc.split("WHY THIS EXISTS")[1].split("WHAT IT BUILDS")[0].strip(),
        "builds": doc.split("WHAT IT BUILDS")[1].split("THE ACCOUNTING")[0].strip(),
        "accounting": doc.split("THE ACCOUNTING")[1].split("THE READING")[0].strip(),
        "reading": doc.split("THE READING")[1].split("ASSUMPTIONS")[0].strip(),
        "assumptions": [ln.strip() for ln in doc.split("ASSUMPTIONS")[1].split("Usage:")[0].splitlines() if ln.strip()],
        "generator": "bin/matrixssl_ablation.py --write",
        "manifest": str(MANIFEST.relative_to(REPO)),
        "variants": list(VARIANTS), "designs": list(DESIGNS), "converted_iterations": CONVERTED,
        "summary": summary, "attribution": attribution, "runs": runs,
    }


FINDING = ("the MatrixSSL residual is the dummy step's fixed operands: rebuilding the dummy "
           "step with evolving operands removes about ninety-five per cent of the per-iteration "
           "gap between a real step and a dummy step, making the doubling in place moves it by "
           "about two per cent, and what remains after both is small and not proportional to "
           "the converted-iteration count")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", nargs=3, metavar=("VARIANT", "SRC", "DST"))
    ap.add_argument("--import", dest="imp", metavar="WORKDIR")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.patch:
        v, src, dst = a.patch
        if v not in PATCHES:
            sys.exit(f"matrixssl_ablation: unknown variant {v}; one of {', '.join(VARIANTS)}")
        patch(v, pathlib.Path(src), pathlib.Path(dst))
        return 0
    if a.imp:
        do_import(pathlib.Path(a.imp))
        return 0
    doc = build()
    if a.check:
        if not OUT.exists():
            print("matrixssl_ablation: no committed record", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text())
        bad = []
        want = {(r["file"]): r["delta_ticks"] for r in old.get("runs", [])}
        for r in doc["runs"]:
            o = want.get(r["file"])
            if o is None or abs(o - r["delta_ticks"]) > 1e-6 * max(1.0, abs(r["delta_ticks"])):
                bad.append(r["file"])
        if len(want) != len(doc["runs"]):
            bad.append(f"run count {len(doc['runs'])} vs committed {len(want)}")
        for dsg, blk in doc["attribution"].items():
            for k, v in blk.items():
                o = old.get("attribution", {}).get(dsg, {}).get(k)
                if v is not None and (o is None or abs(float(o) - v) > 1e-6 * max(1.0, abs(v))):
                    bad.append(f"attribution.{dsg}.{k}")
        if bad:
            print("matrixssl_ablation: differs from committed: " + ", ".join(bad[:8]), file=sys.stderr)
            return 1
        print(f"matrixssl_ablation: check clean ({len(doc['runs'])} runs, "
              f"{len(doc['attribution'])} attributed designs)")
        return 0
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"matrixssl_ablation: wrote {OUT.relative_to(REPO)}")
    for v, blk in doc["summary"].items():
        for dsg, s in blk.items():
            per = s["per_iteration_ticks"]
            print(f"  {v:<11} {dsg:<10} n={s['repeats']}  delta {s['mean_delta_ticks']:>10.1f} "
                  f"[{s['min_delta_ticks']:.0f}, {s['max_delta_ticks']:.0f}]"
                  + (f"  per-iter {per:.1f}" if per is not None else ""))
    for dsg, at in doc["attribution"].items():
        print(f"  {dsg}: real step {at['real_step_ticks']:.0f}, shipped gap {at['shipped_gap_ticks']:.0f} "
              f"({100 * at['shipped_gap_fraction_of_step']:.0f}% of a step), copy term "
              f"{at['copy_term_ticks']:+.0f}, operand term {at['operand_term_ticks']:+.0f}, "
              f"both removed {at['both_removed_gap_ticks']:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
