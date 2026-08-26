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
# TCHES caps a submission at 20 pages including appendices, excluding the
# bibliography (CHES 2026 call for papers). The floor is ours: under it, the
# paper is leaving defensibility in an eprint for no reason.
PAGE_CAP = 20
PAGE_FLOOR = 17
NAMECHECK = REPO / "bin" / "namecheck.py"


_INLINE = re.compile(r"\\(?:emph|texttt|textbf|textit|mathrm|text)\{([^{}]*)\}")


def flat(s: str) -> str:
    """Normalise LaTeX prose so two spellings of one claim compare equal.

    Whitespace-, markup- and case-insensitive, because all three have defeated a
    consistency check in this project. A literal substring test misses a claim split
    across a line break. A whitespace-only test misses one whose words are wrapped in
    \\emph{} or \\texttt{}. And a case-sensitive test misses one that merely starts a
    sentence. Every rule that compares prose normalises through here, on both sides.
    """
    prev = None
    while prev != s:                       # nested \emph{\texttt{..}} needs a fixpoint
        prev = s
        s = _INLINE.sub(r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)  # any surviving control sequence
    s = re.sub(r"[{}$~]", " ", s)
    return " ".join(s.split()).lower()


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

    # A claim the paper must not make in a given place. Unlike [[retired]], which is
    # global with a narrow exemption, this one is scoped positively: the phrase is
    # refused only in the files named by `in_files`. The first use is the anti-survey
    # gate over the section carrying the analyser matrix, where the paper classifies a
    # field it explicitly did not survey and must not be read as claiming otherwise.
    for entry in spec.get("forbidden", []):
        phrase = flat(entry["phrase"])
        scope = set(entry.get("in_files", []))
        for name, text in texts.items():
            if scope and name not in scope:
                continue
            if phrase in flat(text):
                bad.append(f"{name}: forbidden phrase {phrase!r} "
                           f"({entry.get('why', 'no reason recorded')})")

    # A claim that must be made exactly once. This is what makes distributing the
    # limitations safe. The single-designated-place rule in docs/review-standard.md
    # exists because rounds 6 to 8 generated their own work through caveat
    # proliferation; moving each limit next to the claim it bounds keeps the venue's
    # arrangement without reopening that failure, but only if a machine counts.
    for entry in spec.get("once", []):
        phrase = flat(entry["phrase"])
        where = sorted(n for n, text in texts.items() if phrase in flat(text))
        if len(where) != 1:
            bad.append(
                f"claim {phrase!r} must appear in exactly one file, found in "
                f"{len(where)}: {', '.join(where) if where else 'none'}. "
                f"{entry.get('why', '')}")

    # Duplicated prose. Five of the largest deletions this restructure makes are the
    # same passage written twice, and not one of them is a retired claim, so no rule
    # above can see them. A duplicate is not a contradiction, which is why it survives
    # every other gate, but it is how a claim comes to be corrected in one place and
    # left standing in another. main.tex is exempt by default because an abstract's
    # job is to restate the body.
    dup_cfg = spec.get("duplicate")
    if dup_cfg:
        window = int(dup_cfg.get("window", 12))
        exempt_files = set(dup_cfg.get("exempt_files", ["main.tex"]))
        allowed_windows = {flat(a) for a in dup_cfg.get("allow", [])}
        words = {n: flat(text).split() for n, text in texts.items()
                 if n not in exempt_files and not n.startswith("gen/")
                 and n != "numbers.tex"}
        seen: dict[str, set] = {}
        for name, w in words.items():
            for i in range(len(w) - window + 1):
                seen.setdefault(" ".join(w[i:i + window]), set()).add(name)
        # Report one line per duplicated passage, not one per overlapping window: a
        # 28-word duplicate contains seventeen 12-word windows and is one defect.
        reported = set()
        for name, w in words.items():
            i = 0
            while i <= len(w) - window:
                key = " ".join(w[i:i + window])
                peers = seen.get(key, set()) - {name}
                if not peers or key in allowed_windows:
                    i += 1
                    continue
                j = i
                while (j <= len(w) - window
                       and (seen.get(" ".join(w[j:j + window]), set()) - {name}) == peers
                       and " ".join(w[j:j + window]) not in allowed_windows):
                    j += 1
                run = " ".join(w[i:j + window - 1])
                sig = (frozenset(peers | {name}), run)
                if sig not in reported:
                    reported.add(sig)
                    bad.append(
                        f"duplicated in {', '.join(sorted(peers | {name}))}: "
                        f"{len(run.split())} words, {run[:80]!r}")
                i = max(j, i + 1)

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



_LABEL = re.compile(r"\\label\{((?:fig|tab|lst):[A-Za-z0-9:_-]+)\}")
_REF = re.compile(r"\\(?:auto|C|c)?ref\{([^{}]*)\}")
_INPUT = re.compile(r"^[^%\n]*\\input\{([^{}]+)\}", re.M)


def _float_owners(paper: Path) -> tuple[dict[str, str], set[str]]:
    """Map each source file to the sectioning file that owns it, and name the body ones.

    A generated table lives in gen/ but belongs to whichever section \\inputs it, so its
    labels must be attributed there or every generated float looks orphaned. Body files are
    those main.tex inputs before \\appendix; the rest are appendix files.
    """
    main = (paper / "main.tex").read_text(errors="replace")
    m = re.search(r"^\\appendix", main, re.M)   # not the one in the header comment
    cut = m.start() if m else len(main)
    body_inputs = [g.group(1) for g in _INPUT.finditer(main[:cut])]
    owner, body = {}, set()
    for rel in body_inputs:
        name = rel if rel.endswith(".tex") else rel + ".tex"
        body.add(name)
    for src in sorted(paper.rglob("*.tex")):
        name = str(src.relative_to(paper))
        owner[name] = name
    # A file inputted by a section is owned by that section, one level is enough here.
    for src in sorted(paper.rglob("*.tex")):
        name = str(src.relative_to(paper))
        for m in _INPUT.finditer(src.read_text(errors="replace")):
            rel = m.group(1)
            child = rel if rel.endswith(".tex") else rel + ".tex"
            if child in owner and child != name and name != "main.tex":
                owner[child] = name
    return owner, body


def _floats(texts: dict[str, str], paper: Path) -> list[str]:
    """Every float must be referenced, and a body float from the section that defines it.

    Three of the four body floats in this paper were referenced only from appendices, which
    is the shape that makes a float read as decoration: the prose beside the evidence never
    walks the reader through it. A float nothing references at all is a page of paper nobody
    asked for, and this paper carried two.
    """
    if not (paper / "main.tex").exists():
        return []
    owner, body = _float_owners(paper)
    defined: dict[str, str] = {}
    for name, text in texts.items():
        if not name.endswith(".tex"):
            continue
        for m in _LABEL.finditer(text):
            defined[m.group(1)] = owner.get(name, name)
    refs: dict[str, set] = {}
    for name, text in texts.items():
        if not name.endswith(".tex"):
            continue
        home = owner.get(name, name)
        for m in _REF.finditer(text):
            for lab in m.group(1).split(","):
                lab = lab.strip()
                if lab:
                    refs.setdefault(lab, set()).add(home)
    bad = []
    for lab, home in sorted(defined.items()):
        where = refs.get(lab, set())
        if not where:
            bad.append(f"float {lab} (in {home}) is referenced nowhere")
        elif home in body and home not in where:
            bad.append(f"float {lab} sits in {home} and is referenced only from "
                       f"{', '.join(sorted(where))}, never from the section that defines it")
    return bad


def _pages(paper: Path) -> list[str]:
    """The venue's page cap, and the dangling references a split build makes possible.

    TCHES caps a submission at twenty pages including every figure, table and appendix, so
    the cap is a property of the deliverable and belongs in a control rather than in a
    habit. The floor matters too: a submission well under the cap with its evidence in an
    eprint nobody opens is worse than one that spends the space.
    """
    bad = []
    log = paper / "main.log"
    if log.exists():
        n = len(re.findall(r"LaTeX Warning: Reference", log.read_text(errors="replace")))
        if n:
            bad.append(f"{n} dangling reference(s) in the build; a \\Cref to a label that "
                       f"does not exist renders as ?? and no other gate sees it")
    aux = paper / "main.aux"
    if aux.exists():
        m = re.search(r"\\newlabel\{endofcontent\}\{\{[^{}]*\}\{(\d+)\}",
                      aux.read_text(errors="replace"))
        if not m:
            # A control that passes having examined nothing is the failure this corpus
            # already has a name for. Without the label there is no page assertion, so
            # the absence of the label is the failure, not a reason to skip.
            bad.append("no \\label{endofcontent} before the bibliography, so the page "
                       "cap is not measured and this check would pass vacuously")
        else:
            pages = int(m.group(1))
            if pages > PAGE_CAP:
                bad.append(f"content runs to page {pages}, over the {PAGE_CAP}-page cap "
                           f"(figures, tables and appendices included, bibliography "
                           f"excluded)")
            elif pages < PAGE_FLOOR:
                bad.append(f"content ends on page {pages}, under the {PAGE_FLOOR}-page "
                           f"floor: {PAGE_CAP - pages} pages of cap are unspent")
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
          f"{'no retired or forbidden claim survives, every once-claim is made once, '
             'no passage is written twice, every printed ratio reproduces'
             if not cons else '; '.join(cons[:3])}")
    if cons:
        fails.append(f"{len(cons)} consistency violation(s)")

    flt = _floats(src_texts, paper)
    print(f"  floats     {'PASS' if not flt else 'FAIL'}  "
          f"{'every float is referenced, and every body float from its own section'
             if not flt else '; '.join(flt[:3])}")
    if flt:
        fails.append(f"{len(flt)} float(s) unanchored or unreferenced")

    pg = _pages(paper)
    print(f"  pages      {'PASS' if not pg else 'FAIL'}  "
          f"{'within the page cap, no dangling references' if not pg else '; '.join(pg)}")
    if pg:
        fails.append("page budget or dangling reference")

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
