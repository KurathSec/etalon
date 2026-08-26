#!/usr/bin/env python3
"""Anonymity gate for the paper, which git does not track.

The vocabulary firewall (bin/namecheck.py) and the anonymous export
(bin/export.py) both scan the tracked tree, and both exclude paper/ because it is
gitignored. So nothing else checks the paper's own text or its built PDF for the
real project name, an author identity, or a citation into the programme's own
prior work. That gap is invisible while the draft carries no bibliography and no
artifact URL, and it opens the moment either is added. This closes it.

Three scans, all fail-closed once the paper exists:
  1. the digest firewall over the paper source (main.tex, refs.bib, numbers.tex),
     which is exactly the check the tracked tree already gets;
  2. the same firewall over the text extracted from the built PDF, in case a term
     reaches the rendered page that a source scan would miss;
  3. the PDF metadata (Author, Title, Subject, Keywords), which must be empty or
     anonymous, since pdflatex will happily stamp a login name there.

An absent paper is NOT a failure: this runs from `make check` on a machine that
has the gitignored source, and CI, which does not, skips it. But a paper that is
present and scans zero files IS a failure, the same rule the firewall uses, so a
broken extraction cannot read as clean.

Usage: bin/paper_check.py [--paper DIR]
Exit codes: 0 clean or not applicable, 1 a violation, 2 could not run.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NAMECHECK = REPO / "bin" / "namecheck.py"


def _identity_names() -> list[str]:
    """The real project name from identity.toml, which the firewall does not hold.

    The digest firewall guards the programme's cross-repo vocabulary; the
    project's own name is governed by ANON-1 against identity.toml. The paper is
    outside ANON-1's tracked-tree scan, so it must be checked against the same
    source of truth here. The anon name is allowed to appear; the real one is not.
    """
    idp = REPO / "data" / "identity.toml"
    if not idp.exists():
        return []
    return [tomllib.loads(idp.read_text()).get("project_name", "")]


def _scan_identity(texts: dict[str, str]) -> list[str]:
    hits = []
    for name in _identity_names():
        if not name:
            continue
        pat = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
        for where, text in texts.items():
            if pat.search(text):
                hits.append(f"{name!r} in {where}")
    return hits


def _namecheck(path: Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(NAMECHECK), "--paths", str(path)],
                       capture_output=True, text=True)
    m = re.search(r"over (\d+) files", r.stdout)
    n = int(m.group(1)) if m else 0
    if r.returncode != 0:
        return False, (r.stdout + r.stderr).strip().splitlines()[-1]
    if n == 0:
        return False, f"firewall examined zero files under {path}"
    return True, f"firewall clean over {n} file(s)"


def _verdict_drift(texts: dict[str, str]) -> list[str]:
    """Every fix case's committed verdict must not be contradicted anywhere in the prose.

    This exists because the same failure happened three times in one revision cycle. A
    verdict is corrected in the section that owns it and in the summary table, and the
    other four sections keep the old sentence: the paper then says two different things
    about one case, and the contradiction is invisible to every other gate because each
    sentence is individually well-formed and every number in it is a correct macro.

    The check is deliberately literal. For each library, read the outcome recorded in
    results/fix_verification.json, and if that outcome is a withdrawal, fail on any
    surviving prose that grades the case. It cannot catch every phrasing, and it is not
    meant to; it catches the exact restatement that keeps surviving.
    """
    import json
    fv = REPO / "results" / "fix_verification.json"
    if not fv.exists():
        return []
    libs = json.loads(fv.read_text()).get("libraries", {})
    bad = []
    for lib, rec in libs.items():
        outcome = str(rec.get("outcome", "")).lower()
        withdrawn = "not decidable" in outcome or "withdraw" in outcome
        if not withdrawn:
            continue
        # Phrases that grade a case whose verdict is withdrawn.
        graded = [f"{lib}'s fix holds", f"{lib} fix holds",
                  f"{lib}'s fix does hold", f"{lib}: the fix holds"]
        for name, text in texts.items():
            low = text.lower()
            for g in graded:
                if g.lower() in low:
                    bad.append(f"{name}: grades {lib} as holding, but its committed "
                               f"outcome is withdrawn as not decidable")
    return bad


def _consistency(texts: dict[str, str], paper: Path) -> list[str]:
    """Two scans that catch the class of defect blind review kept finding.

    Rounds 6 to 8 of the blind panel produced blocking items dominated by one shape: a claim
    corrected in the body while a stale copy survived in a table, a caption or an appendix,
    and a percentage printed beside a numerator it does not divide. Each is individually
    well formed, every number in it is a correct macro, and no existing gate sees it. The
    rules live in data/paper_consistency.toml so retiring a claim is a commit, not a memory.

    RETIRED: a withdrawn claim must not appear anywhere in the paper source.
    RATIO:   a printed percentage must reproduce from its printed numerator and denominator,
             which is what a reader checking the arithmetic will do.
    """
    spec_p = REPO / "data" / "paper_consistency.toml"
    if not spec_p.exists():
        return []
    spec = tomllib.loads(spec_p.read_text())
    bad = []

    # Whitespace- AND markup-insensitive, because both have defeated this check once each.
    # A literal substring test misses a claim split across a line break; a whitespace-only
    # test misses one whose words are wrapped in \\emph{} or \\texttt{}, which is how a
    # promoted block survived in an appendix while the rule reported clean. Normalise the
    # same way on both sides: unwrap inline font commands keeping their contents, drop the
    # remaining control sequences, then collapse whitespace.
    # Whitespace-, markup- and case-insensitive, because all three have defeated this
    # check. A literal substring test misses a claim split across a line break. A
    # whitespace-only test misses one whose words are wrapped in \emph{} or \texttt{}. And
    # a case-sensitive test misses one that merely starts a sentence: the appendix copy
    # that survived here opened "An \emph{instruction-class} verdict" against a rule
    # written "an instruction-class verdict". Normalise both sides the same way.
    _INLINE = re.compile(r"\\(?:emph|texttt|textbf|textit|mathrm|text)\{([^{}]*)\}")

    def flat(s: str) -> str:
        prev = None
        while prev != s:                       # nested \emph{\texttt{..}} needs a fixpoint
            prev = s
            s = _INLINE.sub(r"\1", s)
        s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)  # any surviving control sequence
        s = re.sub(r"[{}$~]", " ", s)
        return " ".join(s.split()).lower()

    for entry in spec.get("retired", []):
        phrase = flat(entry["phrase"])
        # The passage that performs the withdrawal has to be able to quote the claim it
        # withdraws, or the paper cannot say what it retired. Naming that file explicitly
        # keeps the exemption narrow and visible instead of relying on how the two happen
        # to be capitalised.
        allowed = set(entry.get("allow_in", []))
        for name, text in texts.items():
            if name in allowed:
                continue
            if phrase in flat(text):
                bad.append(f"{name}: retired claim {phrase!r} is still present "
                           f"(withdrawn in {entry.get('retired_in', 'an earlier round')})")

    nums_p = paper / "numbers.tex"
    if nums_p.exists() and spec.get("ratio"):
        src = nums_p.read_text()

        def macro(name):
            m = re.search(r"\\newcommand\{\\%s\}\{([^}]*)\}" % re.escape(name), src)
            if not m:
                return None
            v = m.group(1).replace(",", "").replace("\\%", "").replace("%", "").strip()
            try:
                return float(v)
            except ValueError:
                return None

        for entry in spec["ratio"]:
            n, d, pc = (macro(entry["num"]), macro(entry["den"]), macro(entry["pct"]))
            if None in (n, d, pc) or not d:
                bad.append(f"ratio {entry['num']}/{entry['den']} vs {entry['pct']}: "
                           f"a macro is missing or unparseable, so the check is vacuous")
                continue
            got = abs(n / d) * 100.0
            if abs(got - pc) > entry.get("tol", 0.05):
                bad.append(
                    f"ratio: {entry['num']}={n:g} over {entry['den']}={d:g} is {got:.3f}%, "
                    f"but {entry['pct']} prints {pc:g}% "
                    f"(tolerance {entry.get('tol', 0.05)}). {entry.get('why', '')}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default=str(REPO / "paper" / "tches"))
    args = ap.parse_args()
    paper = Path(args.paper)
    tex = paper / "main.tex"
    if not tex.exists():
        print(f"paper-check: no paper at {paper}, not applicable (not a failure)")
        return 0

    fails = []

    ok, msg = _namecheck(paper)
    print(f"  source     {'PASS' if ok else 'FAIL'}  {msg}")
    if not ok:
        fails.append("paper source")

    # Every .tex under the paper tree, not only the top level. The prose lives in
    # sec/, so a top-level glob checks main.tex and numbers.tex and misses the eleven
    # files that contain the paper. The identity scan had the same blind spot.
    src_texts = {str(p.relative_to(paper)): p.read_text(errors="replace")
                 for p in sorted(list(paper.rglob("*.tex")) + list(paper.rglob("*.bib")))}
    id_hits = _scan_identity(src_texts)
    print(f"  identity   {'PASS' if not id_hits else 'FAIL'}  "
          f"{'no real project name in source' if not id_hits else ', '.join(id_hits)}")
    if id_hits:
        fails.append("identity in source")

    drift = _verdict_drift(src_texts)
    print(f"  verdicts   {'PASS' if not drift else 'FAIL'}  "
          f"{'no prose contradicts a committed verdict' if not drift else '; '.join(drift[:3])}")
    if drift:
        fails.append("prose contradicts a committed verdict")

    cons = _consistency(src_texts, paper)
    print(f"  consistent {'PASS' if not cons else 'FAIL'}  "
          f"{'no retired claim survives, every printed ratio reproduces' if not cons else '; '.join(cons[:3])}")
    if cons:
        fails.append("a retired claim survives or a printed ratio does not reproduce")

    pdf = paper / "main.pdf"
    if pdf.exists() and shutil.which("pdftotext"):
        with tempfile.TemporaryDirectory(prefix="paper-pdf-") as td:
            txt = Path(td) / "pdftext.txt"
            subprocess.run(["pdftotext", str(pdf), str(txt)],
                           capture_output=True, text=True)
            if txt.exists() and txt.stat().st_size > 0:
                ok, msg = _namecheck(Path(td))
                print(f"  pdf-text   {'PASS' if ok else 'FAIL'}  {msg}")
                if not ok:
                    fails.append("pdf text")
                pdf_id = _scan_identity({"pdf": txt.read_text(errors="replace")})
                if pdf_id:
                    print(f"  pdf-ident  FAIL  {', '.join(pdf_id)}")
                    fails.append("identity in pdf")
            else:
                print("  pdf-text   FAIL  pdftotext produced nothing")
                fails.append("pdf text extraction")

        if shutil.which("pdfinfo"):
            info = subprocess.run(["pdfinfo", str(pdf)],
                                  capture_output=True, text=True).stdout
            fields = ("Title", "Author", "Subject", "Keywords", "Creator", "Producer")
            vals = {}
            for field in fields:
                m = re.search(rf"^{field}:[ \t]*(.*?)[ \t]*$", info, re.M)
                vals[field] = (m.group(1).strip() if m else "")
            leaked = []
            # The author must not carry a real name. The title, keywords and
            # subject are public paper content and may be non-empty; the creator
            # and producer are tool strings. No field may carry an identifying
            # name, which the identity scan checks over all of them.
            a = vals["Author"].lower()
            if a and a not in ("anonymous", "anonymous submission"):
                leaked.append(f"Author={vals['Author']!r}")
            leaked += _scan_identity({f"metadata:{k}": v
                                      for k, v in vals.items() if v})
            ok = not leaked
            print(f"  pdf-meta   {'PASS' if ok else 'FAIL'}  "
                  f"{'author anonymous, no identity in metadata' if ok else ', '.join(leaked)}")
            if not ok:
                fails.append("pdf metadata")
    else:
        print("  pdf        SKIP  no built PDF or no pdftotext")

    if fails:
        print(f"paper-check: FAIL ({', '.join(fails)})")
        return 1
    print("paper-check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
