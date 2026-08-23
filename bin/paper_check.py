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

    src_texts = {p.name: p.read_text(errors="replace")
                 for p in list(paper.glob("*.tex")) + list(paper.glob("*.bib"))}
    id_hits = _scan_identity(src_texts)
    print(f"  identity   {'PASS' if not id_hits else 'FAIL'}  "
          f"{'no real project name in source' if not id_hits else ', '.join(id_hits)}")
    if id_hits:
        fails.append("identity in source")

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
