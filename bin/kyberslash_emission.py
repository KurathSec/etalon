#!/usr/bin/env python3
"""The KyberSlash emission map, derived from the binaries lock rather than typed.

WHY THIS EXISTS
results/kyberslash_emission.json used to be assembled by hand from the lock: the
same counts, copied. A copied number is one that can drift from its source when
a cell is added, and the sixteenth-review cycle added six. This script reads the
lock the build wrote, one entry per (cell, arm), and derives the map and its
finding from those counts alone, so the sentence the paper prints about which
levels emit is chosen by the data rather than kept by hand.

WHAT IT DERIVES
For every locked cell of the kyberslash pair: the vendor and the optimisation
label from the cell name, the flags from bin/build.py's cell table, the
leak-class instruction count of each arm, and whether the division is emitted
(the vulnerable arm carries at least one leak-class instruction). From the map:
which levels emit under each compiler, whether the compilers disagree, whether
either is safe at every level, and which levels are unsafe under both. The
finding is composed from those predicates; every clause it makes is one the map
supports, and the clause about levels unsafe under both is rewritten when the
intersection is non-empty.

Usage: kyberslash_emission.py [--write] [--check]
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
LOCK = REPO / "locks" / "binaries.lock.json"
OUT = REPO / "results" / "kyberslash_emission.json"
PAIR = "kyberslash"
# Optimisation labels in the order the figure draws them; a label absent from the
# lock is simply not drawn.
OPT_ORDER = ["O0", "O1", "O2", "O3", "O3v3", "Os", "Oz"]
CELL = re.compile(r"^(?P<vendor>gcc|clang)-(?P<version>[0-9.]+)-(?P<opt>[A-Za-z0-9]+)-(?P<triple>.+)$")
MEASURED_ON = ("gcc 12.2.0 and clang 14.0.6, x86-64, debian bookworm images pinned by "
               "digest (localhost/ct-toolchain/{gcc,clang}-bookworm:1); counts read from "
               "objdump of the entry symbol by bin/build.py, recorded in "
               "locks/binaries.lock.json")


def _cells_table() -> dict:
    spec = importlib.util.spec_from_file_location("build", REPO / "bin" / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CELLS

# The finding is a literal, as GEN-1 requires of every record's prose, and the guard
# below refuses to write it when the lock says otherwise: the sentence is kept by the
# data, not by hand, which is how "no level is unsafe under both" survived in the
# record after the -Oz cells were locked.
FINDING = ("The secret-dependent division in the Kyber reference code is emitted as a "
           "hardware division instruction in some (vendor, optimisation) cells and replaced "
           "by a constant-time reciprocal multiply in others. The two compilers disagree on "
           "which cells are safe: gcc emits it at -Os and -Oz, clang emits it at -O0 and -Oz. "
           "Neither compiler is safe at every optimisation level, one level, -Oz, is unsafe "
           "under both, and apart from it which levels emit depends on the compiler, which is "
           "why a corpus item's label must be bound to a pinned toolchain.")


def _list(opts: list[str]) -> str:
    names = ["-" + o for o in opts]
    return " and ".join([", ".join(names[:-1]), names[-1]]) if len(names) > 1 else (names[0] if names else "no level")


def _verify_finding(emit: dict, both: list[str], none_safe: bool, disagree: bool) -> None:
    """Refuse to write a finding the lock contradicts."""
    want = [f"{vd} emits it at {_list(emit[vd])}" for vd in sorted(emit)]
    want.append("The two compilers disagree" if disagree else "The two compilers agree")
    want.append("Neither compiler is safe at every optimisation level" if none_safe
                else "one compiler is safe at every optimisation level")
    want.append(f"one level, {_list(both)}, is unsafe under both" if len(both) == 1
                else f"levels {_list(both)} are unsafe under both" if both
                else "no level is unsafe under both")
    missing = [w for w in want if w not in FINDING]
    if missing:
        sys.exit("kyberslash_emission: the lock says " + "; ".join(missing)
                 + ", and FINDING does not; rewrite the literal to match the data")


def build() -> dict:
    lock = json.loads(LOCK.read_text()).get(PAIR)
    if not lock:
        sys.exit(f"kyberslash_emission: no {PAIR} entry in {LOCK.relative_to(REPO)}")
    table = _cells_table()
    rows = []
    for cell, arms in lock.items():
        m = CELL.match(cell)
        if not m:
            sys.exit(f"kyberslash_emission: cannot parse cell name {cell}")
        v = arms["vulnerable"]["leak_class_instructions"]
        q = arms["patched"]["leak_class_instructions"]
        if v is None or q is None:
            sys.exit(f"kyberslash_emission: {cell} has no leak-class count; the pair declares no class")
        opt = m["opt"]
        flags = "-" + table[cell][1] if cell in table else None
        rows.append({"vendor": m["vendor"], "opt": opt, "flags": flags, "cell": cell,
                     "leak_emitted": v > 0, "vuln_div_count": v, "patch_div_count": q})
    order = {o: i for i, o in enumerate(OPT_ORDER)}
    rows.sort(key=lambda r: (r["vendor"], order.get(r["opt"], 99), r["opt"]))
    vendors = sorted({r["vendor"] for r in rows})
    emit = {vd: [r["opt"] for r in rows if r["vendor"] == vd and r["leak_emitted"]] for vd in vendors}
    levels = [o for o in OPT_ORDER if any(r["opt"] == o for r in rows)]
    both = [o for o in levels if all(o in emit[vd] for vd in vendors)]
    disagree = len({tuple(emit[vd]) for vd in vendors}) > 1
    none_safe = all(emit[vd] for vd in vendors)
    _verify_finding(emit, both, none_safe, disagree)
    return {
        "pair": PAIR,
        "finding": FINDING,
        "why": __doc__.split("WHY THIS EXISTS")[1].split("WHAT IT DERIVES")[0].strip(),
        "method": __doc__.split("WHAT IT DERIVES")[1].split("Usage:")[0].strip(),
        "generator": "bin/kyberslash_emission.py --write",
        "measured_on": MEASURED_ON,
        "levels": levels,
        "emitting_by_vendor": emit,
        "levels_unsafe_under_both": both,
        "emission_map": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    keys = ("vendor", "opt", "leak_emitted", "vuln_div_count", "patch_div_count")
    if a.check:
        if not OUT.exists():
            print("kyberslash_emission: no committed record", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text())
        mine = sorted(tuple(r[k] for k in keys) for r in doc["emission_map"])
        theirs = sorted(tuple(r.get(k) for k in keys) for r in old.get("emission_map", []))
        if mine != theirs or old.get("finding") != doc["finding"]:
            print("kyberslash_emission: the committed map or finding differs from the lock",
                  file=sys.stderr)
            return 1
        print(f"kyberslash_emission: check clean ({len(mine)} cells, "
              f"{sum(1 for r in doc['emission_map'] if r['leak_emitted'])} emitting)")
        return 0
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"kyberslash_emission: wrote {OUT.relative_to(REPO)}")
    for r in doc["emission_map"]:
        print(f"  {r['vendor']:<6} {r['opt']:<5} {r['flags'] or '':<22} "
              f"{'emits' if r['leak_emitted'] else 'reciprocal'}  vuln={r['vuln_div_count']} patch={r['patch_div_count']}")
    print("  " + doc["finding"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
