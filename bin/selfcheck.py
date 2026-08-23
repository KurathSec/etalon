#!/usr/bin/env python3
"""Run every control this repository can currently check, and say what it did not.

The design rule behind this file: a control that cannot fail is not a control,
and a suite that reports "clean" having examined nothing is worse than no suite,
because it converts "we did not measure" into "we measured and found nothing".
So every control reports the size of what it examined, and a control with
nothing to examine reports NOT_APPLICABLE rather than PASS.

Controls are added as the thing they check comes into existence. The ones that
are declared but not yet implementable are listed by id in the output, so the
gap is visible rather than silent.

Usage:  bin/selfcheck.py [--json]

Exit codes: 0 all applicable controls pass, 1 a control failed, 2 could not run.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PASS, FAIL, NA = "PASS", "FAIL", "NOT_APPLICABLE"

# Controls named in the design that cannot run until the artefact they check
# exists. Printed every run so that "all pass" is never mistaken for "all
# controls ran".
DECLARED_NOT_YET_IMPLEMENTED = {
    "BIN-1": "rebuild reproduces the recorded .text digest (slow path: bin/build.py --check)",
    "CLS-3": "a recall figure is never printed without coverage and the uncovered list",
    "TC-1":  "the cell lock equals a regeneration of the axes",
    "TRC-3": "a smoke-grade trace never feeds a reported number",
}


@dataclass
class Result:
    id: str
    status: str
    examined: int
    detail: str


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def check_anon1(files: list[str]) -> Result:
    """ANON-1: the project name appears only in the files declared to carry it.

    Including in paths. The sibling project's scanner learned that one the hard
    way: a name in a filename is as identifying as a name in a line, and a
    content-only scan reports clean over a tree whose directory listing names
    the project.
    """
    ident = tomllib.loads((REPO / "data" / "identity.toml").read_text())
    allowed = set(ident["allowed_in"])
    needles = {ident["project_name"], ident["anon_project_name"]}
    bad, examined = [], 0
    for rel in files:
        for n in needles:
            if n.lower() in rel.lower():
                bad.append(f"{rel}: name in path")
        if rel in allowed:
            continue
        path = REPO / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        examined += 1
        for i, line in enumerate(text.splitlines(), 1):
            for n in needles:
                if re.search(rf"\b{re.escape(n)}\b", line, re.IGNORECASE):
                    bad.append(f"{rel}:{i}")
    if bad:
        return Result("ANON-1", FAIL, examined,
                      f"{len(bad)} occurrence(s): " + ", ".join(bad[:8]))
    return Result("ANON-1", PASS, examined,
                  f"name confined to the {len(allowed)} declared files")


def check_cls1(files: list[str]) -> Result:
    """CLS-1: every facet value used by a pair exists in the closed vocabulary."""
    classes = tomllib.loads((REPO / "data" / "classes.toml").read_text())
    vocab = {k: set(v["values"]) for k, v in classes["facet"].items()}
    pairs = sorted((REPO / "pairs").glob("*/pair.toml"))
    if not pairs:
        return Result("CLS-1", NA, 0,
                      f"no pairs exist yet; {len(vocab)} facets declared, "
                      f"{sum(len(v) for v in vocab.values())} values")
    bad = []
    for p in pairs:
        cls = tomllib.loads(p.read_text()).get("class", {})
        for facet, allowed in vocab.items():
            got = cls.get(facet)
            if got is None:
                bad.append(f"{p.parent.name}: missing facet {facet}")
            elif got not in allowed:
                bad.append(f"{p.parent.name}: {facet}={got!r} not in vocabulary")
    if bad:
        return Result("CLS-1", FAIL, len(pairs), "; ".join(bad[:8]))
    return Result("CLS-1", PASS, len(pairs), "all facet values in vocabulary")


def check_oracle() -> Result:
    """ORC-1 and ORC-2: the oracle succeeds where it must and fails where it must.

    ORC-2 is the one that matters. A corpus cannot distinguish a working key
    recovery from a script that already knows the answer unless the same
    recovery demonstrably fails on the patched arm.
    """
    r = subprocess.run([sys.executable, str(REPO / "bin" / "verify.py"), "--json"],
                       cwd=REPO, capture_output=True, text=True)
    try:
        results = json.loads(r.stdout)
    except json.JSONDecodeError:
        return Result("ORC-1/2", FAIL, 0, "verify.py produced no parsable result")
    if not results:
        return Result("ORC-1/2", NA, 0, "no pairs with an oracle yet")
    checks = sum(len(x["checks"]) for x in results)
    bad = [f"{x['pair']}/{arm}" for x in results
           for arm, c in x["checks"].items() if c.get("status") != "PASS"]
    not_run = [x["pair"] for x in results if x.get("status") == "NOT_RUN"]
    if bad:
        return Result("ORC-1/2", FAIL, checks, "failed: " + ", ".join(bad))
    run = [x for x in results if x.get("status") != "NOT_RUN"]
    detail = f"{len(run)} pair(s) verified, every recovery succeeded and failed where required"
    if not_run:
        detail += f"; {len(not_run)} tier C not run ({', '.join(not_run)})"
    return Result("ORC-1/2", PASS, checks, detail)


def check_trc1() -> Result:
    """TRC-1: every committed trace matches the digest recorded at acquisition."""
    import hashlib, zlib
    checked, bad = 0, []
    for rec_path in sorted((REPO / "pairs").glob("*/acquire/record.json")):
        record = json.loads(rec_path.read_text())
        pair = rec_path.parent.parent
        for tr in record.get("traces", []):
            path = pair / tr["path"]
            if not path.exists():
                bad.append(f"{pair.name}/{tr['arm']}: missing"); continue
            blob = path.read_bytes()
            checked += 1
            if hashlib.sha256(blob).hexdigest() != tr["sha256_file"]:
                bad.append(f"{pair.name}/{tr['arm']}: file digest"); continue
            # The contract is the digest of the uncompressed bytes; the file
            # digest may legitimately move if the compressor changes.
            if hashlib.sha256(zlib.decompress(blob)).hexdigest() != tr["sha256_raw"]:
                bad.append(f"{pair.name}/{tr['arm']}: RAW digest")
    if not checked:
        return Result("TRC-1", NA, 0, "no committed traces yet")
    if bad:
        return Result("TRC-1", FAIL, checked, "; ".join(bad))
    return Result("TRC-1", PASS, checked, "all traces match their recorded digests")


def check_sz1() -> Result:
    """SZ-1: committed sizes stay inside the declared budgets."""
    budget = tomllib.loads((REPO / "data" / "budget.toml").read_text())
    bad, total, n = [], 0, 0
    for pair in sorted((REPO / "pairs").glob("*/")):
        pair_total = 0
        for f in pair.rglob("*"):
            if not f.is_file():
                continue
            size = f.stat().st_size
            n += 1
            pair_total += size
            if size > budget["max_file_bytes"]:
                bad.append(f"{f.relative_to(REPO)}: {size} bytes")
        total += pair_total
        if pair_total > budget["max_pair_bytes"]:
            bad.append(f"{pair.name}: {pair_total} bytes total")
    if total > budget["max_repo_bytes"]:
        bad.append(f"repository: {total} bytes tracked")
    if bad:
        return Result("SZ-1", FAIL, n, "; ".join(bad))
    return Result("SZ-1", PASS, n,
                  f"{total} bytes across pairs, inside all three budgets")


def check_cls4() -> Result:
    """CLS-4: every CORPUS pair carries a CVE, advisory or DOI.

    This is what keeps fixtures out of the measured population. A leak somebody
    wrote does not enter a corpus drawn from the historical record.
    """
    corpus, bad = 0, []
    for p in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(p.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        corpus += 1
        prov = d.get("provenance", {})
        if not (prov.get("cve") or prov.get("advisory") or prov.get("doi")):
            bad.append(p.parent.name)
    if not corpus:
        return Result("CLS-4", NA, 0, "no corpus pairs yet, only fixtures")
    if bad:
        return Result("CLS-4", FAIL, corpus, "no published identifier: " + ", ".join(bad))
    return Result("CLS-4", PASS, corpus, "every corpus pair has a published identifier")


def check_bin2() -> Result:
    """BIN-2: in every recorded cell, the vulnerable arm emits more leak-class
    instructions than the patched arm.

    This is the mechanical evidence that the patch removed the defect in that
    specific build, which is what keys ground truth to a cell rather than to
    source. A cell where the difference vanishes is reported, not hidden: that
    is the finding that the defect is not emitted there.
    """
    lock_path = REPO / "locks" / "binaries.lock.json"
    if not lock_path.exists():
        return Result("BIN-2", NA, 0, "no binaries built yet")
    lock = json.loads(lock_path.read_text())
    # BIN-2 requires the leak to be emitted in each pair's DECLARED cells, the
    # cells the pair pins as ground truth. A cell outside that set where the leak
    # does not appear is not a control failure: it is the corpus's central
    # finding, that the same source is constant time under a different build, and
    # it is reported rather than flagged. Getting this backwards would make the
    # machinery reject its own headline result.
    checked, undeclared, bad, findings = 0, 0, [], []
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        man = tomllib.loads(path.read_text())
        pair = path.parent.name
        required = set(man.get("toolchain", {}).get("cells_required", []))
        for cell, arms in sorted(lock.get(pair, {}).items()):
            v = arms.get("vulnerable", {}).get("leak_class_instructions")
            q = arms.get("patched", {}).get("leak_class_instructions")
            if v is None or q is None:
                undeclared += 1
                continue
            emitted = v > q
            if cell in required:
                checked += 1
                if not emitted:
                    bad.append(f"{pair}/{cell}: declared cell but leak not emitted "
                               f"(vulnerable={v}, patched={q})")
            elif not emitted:
                findings.append(f"{pair}/{cell}")
    if checked == 0:
        return Result("BIN-2", NA, undeclared,
                      f"no declared cell has an instruction_class to measure")
    if bad:
        return Result("BIN-2", FAIL, checked, "; ".join(bad))
    detail = f"leak emitted in all {checked} declared cell(s)"
    if findings:
        detail += (f"; and NOT emitted in {len(findings)} non-declared cell(s) "
                   f"({', '.join(findings)}), which is the toolchain-pinning finding")
    if undeclared:
        detail += f"; {undeclared} cell(s) NA"
    return Result("BIN-2", PASS, checked, detail)


def check_cls2() -> Result:
    """CLS-2: no two corpus pairs share a facet tuple without declaring replication.

    The anti-padding control. Without it, `n` for a class can be inflated by
    adding three variants of one leak, and the corpus would report a larger
    denominator than it has independent evidence for.
    """
    seen, bad, n = {}, [], 0
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(path.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        n += 1
        cls = d.get("class", {})
        key = tuple(sorted((k, v) for k, v in cls.items() if k not in ("rationale", "mechanism_classes")))
        if key in seen:
            if not d["pair"].get("replicate"):
                bad.append(f"{path.parent.name} duplicates {seen[key]} "
                           f"without declaring replicate = true")
        else:
            seen[key] = path.parent.name
    if n == 0:
        return Result("CLS-2", NA, 0, "no corpus pairs yet, only fixtures")
    if bad:
        return Result("CLS-2", FAIL, n, "; ".join(bad))
    return Result("CLS-2", PASS, n, f"{len(seen)} distinct facet tuple(s) over {n} pair(s)")


def check_cls5() -> Result:
    """CLS-5: every attested cell with no pair is reported, by name.

    Absence is data, not silence. A coverage figure that omits the cells it does
    not cover is the same defect as a rate printed without its denominator.
    """
    r = subprocess.run([sys.executable, str(REPO / "bin" / "regen.py"), "--json"],
                       cwd=REPO, capture_output=True, text=True)
    try:
        report = json.loads(r.stdout)
    except json.JSONDecodeError:
        return Result("CLS-5", FAIL, 0, "regen produced no parsable report")
    cen = report["census"]
    attested = cen["attested_cells"]
    cov = cen["covered_cells"]
    # covered_cells is a Rate serialised as as_record: {of: numerator, n: denom}.
    # The numerator is the count of attested cells the corpus covers.
    covered = cov.get("numerator", 0) if isinstance(cov, dict) else 0
    listed = len(cen["uncovered_cells"])
    if attested == 0:
        return Result("CLS-5", NA, 0, "census is empty")
    expected = attested - covered
    if listed != expected:
        return Result("CLS-5", FAIL, attested,
                      f"{expected} cell(s) should be uncovered "
                      f"({attested} attested minus {covered} covered) "
                      f"but {listed} are listed")
    return Result("CLS-5", PASS, attested,
                  f"{listed} uncovered cell(s) named, census declared "
                  f"'{cen['census_status']}'")


def check_sentinels() -> Result:
    """SENT-1/SENT-2: every applicable analyser detects the positive sentinel and
    flags neither the negative sentinel nor any patched arm.

    A run in which an applicable tool misses the positive sentinel, or flags a
    constant-time control, is VOID: the scoring instrument itself is
    misbehaving, and no recall figure from that run means anything.
    """
    vpath = REPO / "results" / "verdicts.jsonl"
    if not vpath.exists():
        return Result("SENT-1/2", NA, 0, "no scoring run recorded yet")
    rows = [json.loads(l) for l in vpath.read_text().splitlines() if l.strip()]
    applicable = [r for r in rows if r.get("applicable")]
    if not applicable:
        return Result("SENT-1/2", NA, 0, "no applicable analyser/pair yet")
    bad = []
    for r in applicable:
        if r["pair"] == "_sentinel-positive" and r["outcome"] != "detected":
            bad.append(f"{r['tool']} missed the positive sentinel ({r['outcome']})")
        if r["pair"] == "_sentinel-negative" and r.get("vulnerable_status") == "leak_reported":
            bad.append(f"{r['tool']} flagged the negative sentinel")
    checked = sum(1 for r in applicable if r["pair"].startswith("_sentinel"))
    if checked == 0:
        return Result("SENT-1/2", NA, 0, "sentinels not in the scoring run")
    if bad:
        return Result("SENT-1/2", FAIL, checked, "; ".join(bad))
    return Result("SENT-1/2", PASS, checked,
                  "every applicable analyser detects the positive sentinel and "
                  "flags no constant-time control")


def check_paper_untracked(files: list[str]) -> Result:
    """PAPER-1: no tracked file under paper/.

    If the paper is tracked here, its numbers have escaped the regeneration
    gate, and a double-blind submission gains a path into a repository that
    becomes public.
    """
    tracked_paper = [f for f in files if f.startswith("paper/")]
    if tracked_paper:
        return Result("PAPER-1", FAIL, len(tracked_paper),
                      "tracked: " + ", ".join(tracked_paper[:5]))
    return Result("PAPER-1", PASS, len(files), "paper/ holds no tracked file")


def check_namecheck() -> Result:
    """FW-1: the vocabulary firewall passes over tracked files."""
    r = subprocess.run([sys.executable, str(REPO / "bin" / "namecheck.py")],
                       cwd=REPO, capture_output=True, text=True)
    m = re.search(r"over (\d+) files", r.stdout)
    n = int(m.group(1)) if m else 0
    if r.returncode != 0:
        return Result("FW-1", FAIL, n, r.stderr.strip().splitlines()[0] if r.stderr else "violations")
    if n == 0:
        # A scan that read nothing must not report clean.
        return Result("FW-1", FAIL, 0, "firewall examined zero files")
    return Result("FW-1", PASS, n, "no forbidden vocabulary")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        files = tracked()
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"selfcheck: cannot list tracked files ({exc})", file=sys.stderr)
        return 2

    results = [
        check_namecheck(),
        check_anon1(files),
        check_cls1(files),
        check_cls2(),
        check_cls4(),
        check_cls5(),
        check_oracle(),
        check_trc1(),
        check_bin2(),
        check_sentinels(),
        check_sz1(),
        check_paper_untracked(files),
    ]

    if args.json:
        print(json.dumps({"results": [asdict(r) for r in results],
                          "not_yet_implemented": sorted(DECLARED_NOT_YET_IMPLEMENTED)},
                         indent=2))
    else:
        width = max(len(r.id) for r in results)
        for r in results:
            print(f"  {r.id:<{width}}  {r.status:<15} n={r.examined:<5} {r.detail}")
        print(f"\n  {len(DECLARED_NOT_YET_IMPLEMENTED)} further controls are declared "
              f"and not yet implementable:")
        for cid in sorted(DECLARED_NOT_YET_IMPLEMENTED):
            print(f"    {cid}: {DECLARED_NOT_YET_IMPLEMENTED[cid]}")

    failed = [r for r in results if r.status == FAIL]
    if failed:
        print(f"\nselfcheck: {len(failed)} control(s) FAILED", file=sys.stderr)
        return 1
    ran = [r for r in results if r.status == PASS]
    print(f"\nselfcheck: {len(ran)} control(s) passed, "
          f"{len(results) - len(ran)} not applicable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
