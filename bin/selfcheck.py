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
import hashlib
import importlib.util
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
    unavailable = [x for x in results if x.get("runtime_unavailable")]
    if unavailable:
        return Result("ORC-1/2", FAIL, len(results),
                      f"{len(unavailable)} pair(s) not verified: {unavailable[0]['reason']} "
                      f"({', '.join(x['pair'] for x in unavailable)})")
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


def _pinned_cells() -> set[str]:
    """The compiler cells bin/build.py can build, read from that file rather than
    duplicated here, so adding a cell there does not silently narrow this control."""
    src = (REPO / "bin" / "build.py").read_text()
    block = re.search(r"^CELLS = \{(.*?)^\}", src, re.S | re.M)
    return set(re.findall(r'"([^"]+)":\s*\(', block.group(1))) if block else set()


PINNED_CELLS = _pinned_cells()


def check_bin2() -> Result:
    """BIN-2: in every declared cell, the vulnerable arm emits strictly more
    leak-class instructions than the patched arm.

    Scope, so the count is readable: the class is the list the pair declares in
    instruction_class, matched against the disassembly of the pair's entry
    symbol on each arm (whatever the compiler inlined into that symbol is
    therefore counted; what it left in a separate function it calls is not,
    unless that callee is itself named in the class). A class entry matches
    either an opcode or a call target, so a divide lowered to a software helper
    counts on targets without a divide instruction. Entries not in the list are
    not counted, which for the division pairs means a power-of-two lowering to a
    shift does not register: the construct under test is the divide, and a shift
    is the compiler removing it.

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
    checked, undeclared, bad = 0, 0, []
    findings, unlocked, out_of_scope = [], [], []
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        man = tomllib.loads(path.read_text())
        pair = path.parent.name
        required = set(man.get("toolchain", {}).get("cells_required", []))
        # A pair that declares a required cell but has no lock entry is not checked by
        # this control at all. Silence there would read as coverage, so it is named.
        # Two cases, kept apart: a pair whose required cells are pinned compiler cells
        # this artifact builds is a genuine gap in coverage; a pair declaring some
        # other toolchain cell (the OpenSSL-linked pairs, scored on recorded traces)
        # is outside this control's reach by construction and is not a gap.
        if required and pair not in lock:
            (unlocked if required & PINNED_CELLS else out_of_scope).append(pair)
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
    if unlocked:
        detail += (f"; GAP: {len(unlocked)} pair(s) declare a pinned cell but have no "
                   f"locked build ({', '.join(sorted(unlocked))})")
    if out_of_scope:
        detail += (f"; outside this control by construction, declaring a non-pinned "
                   f"toolchain cell: {', '.join(sorted(out_of_scope))}")
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
    manifests = {}
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(path.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        manifests[path.parent.name] = d
    for name, d in sorted(manifests.items()):
        n += 1
        cls = d.get("class", {})
        key = tuple(sorted((k, v) for k, v in cls.items()
                           if k not in ("rationale", "mechanism_classes")))
        if key in seen:
            other = seen[key]
            # The replication is declared if EITHER pair names the other. The
            # reproduction (ecdsa-nonce) declaring replicate=minerva is the
            # natural direction, and the check must not depend on which pair it
            # happened to visit first.
            this_ok = d["pair"].get("replicate") and d["pair"].get("replicates") == other
            other_ok = (manifests[other]["pair"].get("replicate") and
                        manifests[other]["pair"].get("replicates") == name)
            # Three or more pairs can share a cell: a reproduction, a real-library
            # build, and the imported dataset they both replicate. They declare it
            # by naming the same common ancestor, not each other, so the check is
            # also satisfied when both declare replicate and name the same target.
            common_ok = (d["pair"].get("replicate")
                         and manifests[other]["pair"].get("replicate")
                         and d["pair"].get("replicates")
                         == manifests[other]["pair"].get("replicates"))
            if not (this_ok or other_ok or common_ok):
                bad.append(f"{name} and {other} share a facet tuple; neither "
                           f"declares replicate = true naming the other")
        else:
            seen[key] = name
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


def check_cls6() -> Result:
    """CLS-6: every pair with a local recovery declares the channel that recovery
    consumes, and any pair whose certification runs on a channel other than its
    declared observable is reported by name.

    A pair can carry two co-located leaks. ecdsa-address does: a secret-indexed
    table access, which is the mechanism it covers in the census and what the
    instruction-class tools are pointed at, and a bit-length timing channel in the
    same function, which is what its lattice recovery actually consumes. Its tier
    therefore certifies the nonce bit-length as exploitable, not the address trace.
    That distinction was prose only, and prose drifts; this makes it a declared
    field the machinery checks, so the corpus cannot quietly claim an
    address-channel certification it has not performed.
    """
    classes = tomllib.loads((REPO / "data" / "classes.toml").read_text())
    allowed = set(classes["facet"]["observable"]["values"])
    missing, badvalue, divergent, n = [], [], [], 0
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        man = tomllib.loads(path.read_text())
        name = path.parent.name
        chan = man.get("class", {}).get("certification_channel")
        obs = man.get("class", {}).get("observable")
        if not man.get("recovery", {}).get("inputs"):
            # No local recovery: the pair certifies nothing here, so the field must
            # be absent rather than asserting a channel no artifact exercises.
            if chan is not None:
                badvalue.append(f"{name}: declares a certification channel but has "
                                f"no local recovery inputs")
            continue
        n += 1
        if chan is None:
            missing.append(name)
        elif chan not in allowed:
            badvalue.append(f"{name}: certification_channel={chan!r} not in vocabulary")
        elif chan != obs:
            divergent.append(f"{name} (observable {obs}, certified through {chan})")
    if missing or badvalue:
        return Result("CLS-6", FAIL, n,
                      "; ".join(([f"missing certification_channel: "
                                  f"{', '.join(missing)}"] if missing else []) + badvalue))
    if n == 0:
        return Result("CLS-6", NA, 0, "no pair carries a local recovery")
    detail = f"all {n} locally certified pair(s) declare their channel"
    if divergent:
        detail += (f"; certification diverges from the declared observable on "
                   f"{len(divergent)}: {'; '.join(divergent)}")
    return Result("CLS-6", PASS, n, detail)


def check_stat1() -> Result:
    """STAT-1: every dudect verdict rests on a permutation row computed from the
    samples that are on disk now, and every committed dump has such a row.

    The verdicts moved onto a permutation null whose record is minutes of compute,
    so nothing regenerates it on the way to a build. That makes silent drift the
    obvious failure: an arm re-acquired, its row left behind, and the paper still
    quoting the old p-value. Each row carries the digest of the dump it was computed
    from, and this compares them, which is cheap enough to run every time.
    """
    rec = REPO / "results" / "dudect_permutation.json"
    raw = sorted((REPO / "results" / "raw").glob("*.dudect.bin.gz"))
    # The fix-verification dumps live in their own directory with their own record, and
    # their statistics reach the paper's headline. A glob written for the corpus dumps
    # does not see them, which is how a set of committed samples ends up with no control
    # tying it to the numbers derived from it.
    fixdig, fixbad = {}, []
    fvp = REPO / "results" / "fix_verification.json"
    if fvp.exists():
        _fv = json.loads(fvp.read_text())
        fixdig = (_fv.get("libraries", {}).get("matrixssl", {})
                  .get("measurements_full_report", {}).get("dump_sha256", {}))
    for f in sorted((REPO / "results" / "raw" / "matrixssl").glob("*.bin.gz")):
        want = fixdig.get(f.name)
        if want is None:
            fixbad.append(f"{f.name}: committed with no digest in its record")
        elif want != hashlib.sha256(f.read_bytes()).hexdigest():
            fixbad.append(f"{f.name}: bytes differ from the record's digest")
    if not rec.exists():
        return Result("STAT-1", NA, 0, "no permutation record yet")
    rows = json.loads(rec.read_text()).get("rows", [])
    by_path = {r["path"]: r for r in rows}
    stale, missing, undigested = [], [], []
    for dump in raw:
        rel = str(dump.relative_to(REPO))
        row = by_path.pop(rel, None)
        if row is None:
            missing.append(rel)
            continue
        want = row.get("sha256")
        if not want:
            undigested.append(rel)
        elif want != hashlib.sha256(dump.read_bytes()).hexdigest():
            stale.append(rel)
    orphan = sorted(by_path)
    if not raw:
        return Result("STAT-1", NA, 0, "no committed dumps")
    if fixbad:
        return Result("STAT-1", FAIL, len(raw) + len(fixdig),
                      "fix-verification dumps disagree with their record: "
                      + "; ".join(fixbad[:3]))
    if stale or missing or orphan:
        parts = []
        if stale:
            parts.append(f"{len(stale)} row(s) computed from different bytes than the "
                         f"dump on disk: {', '.join(stale[:3])}")
        if missing:
            parts.append(f"{len(missing)} dump(s) with no verdict row: "
                         f"{', '.join(missing[:3])}")
        if orphan:
            parts.append(f"{len(orphan)} row(s) whose dump is gone: "
                         f"{', '.join(orphan[:3])}")
        return Result("STAT-1", FAIL, len(raw), "; ".join(parts))
    detail = (f"all {len(raw)} corpus dump(s) match the verdict row computed from them, "
              f"and all {len(fixdig)} fix-verification dump(s) match their record")
    if undigested:
        detail += (f"; {len(undigested)} row(s) predate the digest field and are "
                   f"unchecked, regenerate with bin/dudect_permute.py --assemble")
    return Result("STAT-1", PASS, len(raw), detail)


def check_cls7() -> Result:
    """CLS-7: every corpus pair's class tuple matches an attested census cell, and the
    facet keys the census matches on are exactly the closed vocabulary.

    CLS-5 checks that the coverage arithmetic is self-consistent, and that is not the
    same thing. When a new key was added to a pair's [class] block, every covered tuple
    grew a sixth element, matched no five-facet census cell, and coverage silently fell
    from 7/11 to 3/11 while the uncovered list grew to name cells that pairs already
    covered. CLS-5 passed throughout, because 11 - 3 = 8 is as consistent as 11 - 7 = 4.
    This control checks the join itself: a corpus pair that covers no attested cell is
    either a census gap or a matcher bug, and either way it must be named, not absorbed.
    """
    classes = tomllib.loads((REPO / "data" / "classes.toml").read_text())
    facets = set(classes.get("facet", {}))
    entries = REPO / "data" / "census" / "entries.jsonl"
    if not entries.exists():
        return Result("CLS-7", NA, 0, "no census to join against")
    attested = set()
    for line in entries.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("adjudication") == "included" and r.get("facets"):
            attested.add(tuple(sorted(r["facets"].items())))
    if not attested:
        return Result("CLS-7", NA, 0, "census attests no cell")
    orphans, n = [], 0
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        man = tomllib.loads(path.read_text())
        if man.get("pair", {}).get("role") != "corpus":
            continue
        n += 1
        cls = {k: v for k, v in man.get("class", {}).items() if k in facets}
        if tuple(sorted(cls.items())) not in attested:
            missing = sorted(facets - set(cls))
            orphans.append(f"{path.parent.name}"
                           + (f" (missing facet(s): {', '.join(missing)})" if missing
                              else " (facets present but no census cell matches)"))
    if orphans:
        return Result("CLS-7", FAIL, n,
                      f"{len(orphans)} corpus pair(s) join to no attested census cell: "
                      + "; ".join(orphans))
    return Result("CLS-7", PASS, n,
                  f"all {n} corpus pair(s) join to an attested cell over the "
                  f"{len(facets)} vocabulary facets")


def check_meta1() -> Result:
    """META-1: no control reports PASS having examined nothing.

    This file opens by stating that a suite reporting clean over nothing is worse
    than no suite, because it converts "we did not measure" into "we measured and
    found nothing". That was a design rule and nothing enforced it. It is enforced
    here, over this run's own results, because the rule is worth exactly as much as
    its enforcement: a control whose subject disappears silently starts passing, and
    a passing control is invisible.
    """
    # Filled in by the runner once every other control has produced its result;
    # a control cannot examine the suite it is part of before that suite exists.
    return Result("META-1", NA, 0, "evaluated after the other controls")


def evaluate_meta1(results: list) -> Result:
    """The real META-1, over the results the suite just produced."""
    hollow = [r for r in results
              if r.status == PASS and r.examined == 0 and r.id != "META-1"]
    considered = [r for r in results if r.id != "META-1"]
    if hollow:
        return Result("META-1", FAIL, len(considered),
                      "control(s) passed having examined nothing, which reports "
                      "'we did not measure' as 'we measured and found nothing': "
                      + ", ".join(r.id for r in hollow))
    return Result("META-1", PASS, len(considered),
                  f"every passing control examined at least one item "
                  f"({sum(r.examined for r in considered)} items across "
                  f"{len(considered)} controls)")


def check_inst1() -> Result:
    """INST-1: the permutation null, the leak-class counter and the information measure each
    demonstrate, on committed inputs whose answer is known, that they can return BOTH a loud
    positive and a quiet negative.

    The corpus already demands this of the analysers it scores: SENT-1 and SENT-2
    void a tool's rows unless it detects the planted sentinel and stays clean on the
    certified one, at the same build and invocation. The demand was never turned
    inward, and that asymmetry is where a whole class of error lives.

    The class: for a measurement that seeks a null, an instrument that fails
    produces the same observation as the result being sought. A profiler whose
    binary never loaded reports identical counts between two classes, which reads as
    'the difference is microarchitectural'. A checker that iterates an absent field
    reports no discrepancies. A correlation computed against the wrong key returns
    an AUC of one half, which reads as 'the timing carries no information'. An
    instruction counter pointed at the wrong symbol reports a division-free build.
    Each of those is a clean result, and this corpus's findings are largely clean
    results, so nothing downstream would question them.

    The three are NAMED rather than quantified over, in this docstring, in the controls
    table it generates and in the paper. "Every instrument the corpus reports through" was
    what all three said, and it is a quantifier nothing enforces: the set of instruments
    whose clean readings the paper reports is not derivable from this function, so the
    equality was asserted. A list can be checked against the paper by reading it.

    A one-sided check cannot catch it, because the failure IS the quiet side. So
    every instrument here is exercised twice, on a positive whose answer is known
    loud and a negative whose answer is known quiet, from committed inputs.
    """
    checks, bad = [], []

    # 1. The permutation null: must reject the planted sentinel and not reject the
    #    certified-constant-time one. An instrument that cannot reject anything
    #    would silently mark every arm clean.
    try:
        spec = importlib.util.spec_from_file_location(
            "dudect_permute", REPO / "bin" / "dudect_permute.py")
        dp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dp)
        pos = REPO / "results" / "raw" / "_sentinel-positive_vulnerable.dudect.bin.gz"
        neg = REPO / "results" / "raw" / "_sentinel-negative_patched.dudect.bin.gz"
        if pos.exists() and neg.exists():
            rp = dp.permute(pos, perms=200, n_batches=dp.DECLARED_BATCHES)
            rn = dp.permute(neg, perms=200, n_batches=dp.DECLARED_BATCHES)
            checks.append("permutation null")
            if rp.get("p_value", 1.0) > 0.05:
                bad.append(f"permutation null did not reject the planted sentinel "
                           f"(p={rp.get('p_value')})")
            if rn.get("p_value", 0.0) <= 0.05:
                bad.append(f"permutation null rejected the certified-clean arm "
                           f"(p={rn.get('p_value')})")
    except Exception as exc:
        bad.append(f"permutation null could not be exercised: {exc}")

    # 2. The leak-class counter, exercised as THE SCRIPT THE PAPER REPORTS THROUGH.
    #    It must count a division where one is emitted and none where it is not. Both
    #    textprints are committed, so this needs no build and no container.
    #
    #    An earlier version of this check reimplemented the count here, matching the
    #    mnemonic only. That is a stand-in, and a weaker one than its subject in the
    #    exact place that matters: bin/build.py also matches the CALL TARGET, because
    #    on a target with no divide instruction the compiler emits __udivsi3 or
    #    __aeabi_uidiv and a mnemonic-only counter reports a division-free build. The
    #    stand-in would have passed its own quiet check on such a build while the real
    #    counter found the division, which is precisely the quiet failure INST-1 was
    #    written to catch. It now drives bin/build.py's counter.
    try:
        classes = ["div", "idiv", "divl", "divw"]
        emit_p = (REPO / "locks" / "textprints" / "kyberslash"
                  / "gcc-12.2.0-Os-x86_64-linux-gnu" / "vulnerable.asm")
        quiet_p = (REPO / "locks" / "textprints" / "kyberslash"
                   / "gcc-12.2.0-O2-x86_64-linux-gnu" / "vulnerable.asm")
        if emit_p.exists() and quiet_p.exists():
            spec = importlib.util.spec_from_file_location(
                "ct_build", REPO / "bin" / "build.py")
            bl = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bl)
            def count(text):
                return bl.count_leak_class(text, classes)["leak_class_instructions"]
            checks.append("leak-class counter (bin/build.py)")
            if count(emit_p.read_text()) < 1:
                bad.append("leak-class counter found no division in a cell recorded "
                           "as emitting one")
            if count(quiet_p.read_text()) != 0:
                bad.append("leak-class counter found a division in a cell recorded "
                           "as emitting none")
    except Exception as exc:
        bad.append(f"leak-class counter could not be exercised: {exc}")

    # 3. The information measure, exercised as the SCRIPT THE PAPER REPORTS THROUGH.
    #    An earlier version of this check re-implemented an AUC over synthetic data and
    #    showed that *an* implementation can see and not see an association. That proves
    #    nothing about bin/exploit_budget.py, which is what produces the numbers, and the
    #    docstring above claims this check "would have caught a trace scored against the
    #    wrong key" -- which it would not have, because it never called that script. So it
    #    now drives the real instrument on committed inputs, both ways: the libgcrypt
    #    vulnerable trace with the key its own recovery recovered (known loud), and the
    #    same trace with a key that does not belong to it (known quiet). The quiet side is
    #    the one that matters: a mismatched key returns an AUC of one half, which reads as
    #    "the timing carries no information about the secret".
    try:
        trace = REPO / "pairs" / "libgcrypt-minerva" / "traces" / "vulnerable.csv.z"
        rec = REPO / "pairs" / "libgcrypt-minerva" / "acquire" / "record.json"
        if trace.exists() and rec.exists():
            spec = importlib.util.spec_from_file_location(
                "exploit_budget", REPO / "bin" / "exploit_budget.py")
            eb = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(eb)
            claim = json.loads(rec.read_text())["recovery"]["vulnerable_1_8_4"]
            right = claim.split("recovered d=")[1].split(";")[0].strip()
            # Any other valid scalar serves as the negative: what is being tested is that
            # the measure collapses to one half when the labels it derives are wrong.
            wrong = "%064x" % ((int(right, 16) ^ 0xdeadbeef) % (2 ** 256))
            checks.append("information measure (bin/exploit_budget.py)")
            loud = eb.analyse(trace, int(right, 16))["auc_time_vs_short_nonce"]
            quiet = eb.analyse(trace, int(wrong, 16))["auc_time_vs_short_nonce"]
            if abs(loud - 0.5) < 0.15:
                bad.append(f"information measure did not see the association its own "
                           f"recovery certifies (AUC {loud:.4f} on the key that recovers)")
            if abs(quiet - 0.5) > 0.10:
                bad.append(f"information measure saw an association under a key that does "
                           f"not label this trace (AUC {quiet:.4f}); the measure is not "
                           f"reading the secret it claims to")
    except Exception as exc:
        bad.append(f"information measure could not be exercised: {exc}")

    if not checks:
        return Result("INST-1", NA, 0, "no instrument could be exercised")
    if bad:
        return Result("INST-1", FAIL, len(checks), "; ".join(bad))
    return Result("INST-1", PASS, len(checks),
                  f"{len(checks)} instrument(s) exercised on a known-loud positive "
                  f"and a known-quiet negative: {', '.join(checks)}")


def check_doc1() -> Result:
    """DOC-1: the built PDF is newer than every source it is built from.

    A LaTeX failure leaves the PREVIOUS main.pdf in place. Every downstream check then
    reads that file and passes: the page count is a real page count, the log has no
    undefined references, the text has no NA. The build failed and the evidence of
    success is a stale artifact, which is the same shape as an instrument that fails
    quietly (INST-1) one layer out. This compares mtimes, which is cheap and is the
    check that catches it.

    The paper tree is gitignored, so this control is NOT APPLICABLE where the paper is
    absent, and says so rather than passing over it.

    Both targets are checked. The submission and the eprint share one body, so building
    only one of them lets the other rot, and a stale eprint passing silently is this
    control's own failure mode turned on the build it was written to guard.
    """
    tches = REPO / "paper" / "tches"
    if not tches.exists():
        return Result("DOC-1", NA, 0, "no paper tree in this checkout")
    targets = [tches / "main.pdf", tches / "main-eprint.pdf"]
    present = [t for t in targets if t.exists()]
    if not present:
        return Result("DOC-1", FAIL, 0, "paper sources present but no PDF was ever built")
    srcs = (list(tches.glob("*.tex")) + list((tches / "sec").glob("*.tex"))
            + list((tches / "shared").glob("*.tex"))
            + list((tches / "gen").glob("*.tex")))
    srcs = [f for f in srcs if f.exists()]
    if not srcs:
        return Result("DOC-1", NA, 0, "no paper sources to compare against")
    missing = [t.name for t in targets if not t.exists()]
    if missing:
        return Result("DOC-1", FAIL, len(srcs),
                      f"{', '.join(missing)} was never built, so nothing checks it")
    bad = []
    for pdf in targets:
        pdf_m = pdf.stat().st_mtime
        stale = sorted(f.name for f in srcs if f.stat().st_mtime > pdf_m)
        if stale:
            bad.append(f"{pdf.name} is older than {len(stale)} of its sources "
                       f"({', '.join(stale[:3])})")
    if bad:
        return Result("DOC-1", FAIL, len(srcs),
                      "a check reading these is reading a previous build: "
                      + "; ".join(bad))
    return Result("DOC-1", PASS, len(srcs),
                  f"both PDFs are newer than all {len(srcs)} sources they are built from")


def check_sentinels() -> Result:
    """SENT-1/SENT-2: every applicable analyser detects the positive sentinel and does
    not flag the negative sentinel.

    The scope is the two synthetic sentinels and nothing else. This docstring used to
    add "nor any patched arm", which the code has never checked and must not: the taint
    checker legitimately flags the nonce patched arms, reporting the library's own
    internal branch on the secret, and those rows are scored rather than voided. A
    control that claimed to void them would have deleted the paper's own
    policy-versus-exploit finding. The sentinels qualify the analyser, not the corpus.

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


def check_repeatability() -> Result:
    """REPT-1: the committed re-acquisition record matches its generator.

    results/repeatability.json compares two acquisitions of the same arm, and the
    numbers it feeds into the body are counts of agreement. A count of agreement
    that drifts from its generator is the worst kind to leave unchecked, because
    drift moves it in the reassuring direction as easily as the other one.

    It is NOT a between-acquisition bound, and this docstring said "the only place
    this paper compares two acquisitions" while the body says the opposite: most of
    these arms are rebuilt at gain one, so most pairs here are two acquisitions of
    two binaries. The corpus-wide between-acquisition record, repeats of one binary,
    is results/matrixssl_repeats.json and exists only for the fix case.
    """
    r = subprocess.run([sys.executable, str(REPO / "bin" / "repeatability.py"),
                        "--check"], cwd=REPO, capture_output=True, text=True)
    m = re.search(r"\((\d+) arms\)", r.stdout)
    n = int(m.group(1)) if m else 0
    if r.returncode != 0:
        return Result("REPT-1", FAIL, n,
                      (r.stderr or r.stdout).strip().splitlines()[-1][:120]
                      if (r.stderr or r.stdout).strip() else "generator disagrees")
    return Result("REPT-1", PASS, n,
                  "committed re-acquisition record reproduces from its generator")


def _generator_script(record: dict) -> str | None:
    """The bin/*.py a results record names as its generator, or None.

    Only a top-level `generator` string counts, and only when that script plausibly
    WRITES the record: its source must mention the record's basename or carry a
    "finding" key literal. A record assembled by hand from a script's stdout says so
    in its generator field ("by hand") and is skipped, because its prose is the
    author's and not the script's.
    """
    gen = record.get("generator")
    if not isinstance(gen, str) or "by hand" in gen:
        return None
    m = re.search(r"bin/([A-Za-z0-9_]+\.py)", gen)
    return m.group(1) if m else None


def _string_corpus(script: pathlib.Path) -> str:
    """Every string literal in a script, in source order, whitespace-normalised, with
    digit-bearing tokens removed so an interpolated number never breaks a window."""
    import ast
    tree = ast.parse(script.read_text())
    parts = [n.value for n in ast.walk(tree)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return _prose_norm(" ".join(parts))


def _prose_norm(s: str) -> str:
    toks = [w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()
            if not any(c.isdigit() for c in w)]
    return " ".join(toks)


def check_gen1() -> Result:
    """GEN-1: every prose field of a generated record appears among its generator's string literals.

    The failure this catches happened twice in one round: a generator's `reading` was
    rewritten to withdraw a claim, and its committed results file kept the retired
    text, so the paper's own pointer led a reader to the withdrawn claim. Re-running
    the generator is not always possible, because most of them measure, so this is a
    STATIC check: for each results/*.json whose `generator` names a bin/*.py, every
    six-word window of each prose field (finding, why, reading, *note) must occur in
    the concatenation of that script's string literals. Digit-bearing tokens are
    dropped on both sides so a formatted number cannot break a window. A record whose
    prose was edited by hand to say something its generator does not say fails here,
    which is the point: the record is the generator's output or it is nothing.
    """
    WINDOW = 6
    examined, bad, skipped = 0, [], []
    for rp in sorted((REPO / "results").glob("*.json")):
        try:
            rec = json.loads(rp.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        script = _generator_script(rec)
        if not script:
            continue
        sp = REPO / "bin" / script
        if not sp.exists():
            bad.append(f"{rp.name}: generator bin/{script} does not exist")
            continue
        src = sp.read_text()
        if rp.name not in src and '"finding"' not in src:
            skipped.append(f"{rp.name} (bin/{script} does not write it)")
            continue
        corpus = _string_corpus(sp)
        for key, val in rec.items():
            if not isinstance(val, str):
                continue
            if key not in ("finding", "why", "reading") and not key.endswith("note"):
                continue
            words = _prose_norm(val).split()
            if len(words) < WINDOW:
                continue
            examined += 1
            missing = [" ".join(words[i:i + WINDOW])
                       for i in range(len(words) - WINDOW + 1)
                       if " ".join(words[i:i + WINDOW]) not in corpus]
            if missing:
                bad.append(f"{rp.name}.{key}: {len(missing)} window(s) absent from "
                           f"bin/{script}, first: '{missing[0]}'")
    if bad:
        return Result("GEN-1", FAIL, examined, "; ".join(bad)[:400])
    if examined == 0:
        return Result("GEN-1", NA, 0, "no generated record carries a prose field")
    return Result("GEN-1", PASS, examined,
                  f"{examined} prose field(s) reproduce from their generators' literals"
                  + (f"; {len(skipped)} record(s) hand-assembled, skipped" if skipped else ""))


def check_gen2() -> Result:
    """GEN-2: every generator with a --check mode reproduces its committed record.

    The cheap, dynamic half of GEN-1: bin/repeatability.py, bin/analyser_table.py and
    bin/host_facts.py each re-derive their record from committed inputs in seconds and
    compare. bin/fix_report.py --check is the same discipline and is exercised by STAT-1
    and tests/unit/test_fix_report.py rather than here, because its permutations take
    minutes; bin/build.py --check needs the toolchain images and is BIN-1.
    """
    checks = (("repeatability", ["bin/repeatability.py", "--check"]),
              ("analyser_table", ["bin/analyser_table.py", "--check"]),
              ("host_facts", ["bin/host_facts.py", "--check"]),
              ("matrixssl_report", ["bin/matrixssl_report.py",
                                    "results/raw/matrixssl/repeats", "--check"]))
    bad, skipped = [], []
    for name, cmd in checks:
        r = subprocess.run([sys.executable, *cmd], cwd=REPO,
                           capture_output=True, text=True)
        if r.returncode == 2 and name == "host_facts":
            # The host record can only be re-captured on the acquisition host. On
            # any other machine the check is not applicable, and host_facts says
            # so with exit 2 rather than reporting the other machine as drift.
            skipped.append(f"{name} (not the acquisition host)")
            continue
        if r.returncode != 0:
            tail = (r.stderr or r.stdout).strip().splitlines()
            bad.append(f"{name}: {tail[-1][:100] if tail else 'nonzero exit'}")
    if bad:
        return Result("GEN-2", FAIL, len(checks), "; ".join(bad))
    return Result("GEN-2", PASS, len(checks) - len(skipped),
                  "every --check generator reproduces its committed record: "
                  + ", ".join(n for n, _ in checks if not any(n in k for k in skipped))
                  + (f"; skipped {', '.join(skipped)}" if skipped else ""))


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
        check_cls6(),
        check_cls7(),
        check_stat1(),
        check_inst1(),
        check_doc1(),
        check_oracle(),
        check_trc1(),
        check_bin2(),
        check_sentinels(),
        check_sz1(),
        check_paper_untracked(files),
        check_repeatability(),
        check_gen1(),
        check_gen2(),
    ]

    # META-1 is evaluated last, over the results the suite just produced.
    results.append(evaluate_meta1(results))

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
