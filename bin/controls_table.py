#!/usr/bin/env python3
"""Generate the controls appendix table from bin/selfcheck.py itself.

The paper stated a count ("twelve controls") without ever listing them, so a
reader could not check what the machinery actually enforces. This emits the list
from the control functions' own docstrings and from the declared-but-not-yet-
implemented map, so the table cannot drift from the code that runs: adding a
control to selfcheck.py adds a row here, and the count in the paper is a macro
over the same source.

Writes paper/tches/gen/controls-table.tex.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO / "bin" / "selfcheck.py"
OUT = REPO / "paper" / "tches" / "gen" / "controls-table.tex"

TEX = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#", "$": r"\$"}


def esc(s: str) -> str:
    for a, b in TEX.items():
        s = s.replace(a, b)
    return s


def implemented(src: str) -> list[tuple[str, str]]:
    """(id, one-line description) for every control function, in source order."""
    rows = []
    # A control's docstring opens with its id, either as "CLS-1:" or as the
    # "ORC-1 and ORC-2:" pair form; accept both so no control is silently dropped
    # from the table while still being counted by selfcheck.
    pat = r'\n\s*"""([A-Z][A-Z0-9\-]*(?:\s*(?:and|/)\s*[A-Z][A-Z0-9\-]*)*):\s*(.*?)(?:"""|\n\s*\n)'
    for m in re.finditer(pat, src, re.S):
        cid = " ".join(m.group(1).split())
        desc = " ".join(m.group(2).replace('"""', " ").split()).rstrip(".")
        if cid and desc:
            rows.append((cid, desc))
    return rows


def declared(src: str) -> list[tuple[str, str]]:
    block = re.search(r"DECLARED_NOT_YET_IMPLEMENTED\s*=\s*\{(.*?)\}", src, re.S)
    if not block:
        return []
    return [(m.group(1), " ".join(m.group(2).split()))
            for m in re.finditer(r'"([^"]+)":\s*"([^"]+)"', block.group(1))]


# Controls on the deliverable rather than on any measurement: anonymity, the
# gitignore boundary under paper/, and the cross-repo vocabulary firewall. They are
# enforced on every invocation like the rest, but they guard the submission, not a
# reported number, so they are grouped apart instead of padding the list a reader
# consults to judge the measurements.
DELIVERABLE = {"ANON-1", "PAPER-1", "FW-1"}


def main() -> int:
    src = SRC.read_text()
    impl, decl = implemented(src), declared(src)
    meas = [r for r in impl if r[0] not in DELIVERABLE]
    deliv = [r for r in impl if r[0] in DELIVERABLE]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\caption{The controls, generated from \texttt{bin/selfcheck.py} by "
        r"\texttt{bin/controls\_table.py}. \emph{Enforced} controls run on every "
        r"invocation and must pass; \emph{on demand} ones run and record a result but are "
        r"too slow for every invocation (BIN-1 writes results/bin1\_check.json); "
        r"\emph{declared} ones are specified and named but "
        r"not yet implementable here, and are listed rather than omitted so the gap "
        r"is visible. The last group guards the submission itself rather than any "
        r"measurement.}",
        r"\label{tab:controls}",
        r"\begin{tabular}{@{}l l p{0.62\linewidth}@{}}",
        r"\toprule",
        r"Control & Status & What it enforces \\",
        r"\midrule",
    ]
    for cid, desc in meas:
        lines.append(f"\\texttt{{{esc(cid)}}} & enforced & {esc(desc)} \\\\")
    for cid, desc in decl:
        # BIN-1 is not "not yet implementable": it runs, and its result is committed.
        # Calling it declared beside a caption that defines declared as unimplementable
        # contradicts the section that reports it having run, so it gets its own status.
        status = "on demand" if cid.startswith("BIN-1") else "declared"
        lines.append(f"\\texttt{{{esc(cid)}}} & {status} & {esc(desc)} \\\\")
    if deliv:
        lines += [r"\midrule",
                  r"\multicolumn{3}{@{}l}{\emph{On the deliverable, not on a "
                  r"measurement}} \\"]
        for cid, desc in deliv:
            lines.append(f"\\texttt{{{esc(cid)}}} & enforced & {esc(desc)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"controls_table: wrote {OUT} ({len(impl)} enforced, {len(decl)} declared)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
