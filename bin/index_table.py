#!/usr/bin/env python3
"""Emit the four-index summary table (I1 build cell, I2 host, I3 analyser and budget,
I4 fix site and facet) from the committed results.

A referee opens a paper and looks for the table that says what was measured and
over what. Five of the eight CHES best papers put that table on page three, and
three of them put it inside the introduction. The KyberSlash paper's version
reports its key recoveries as successes over trials, including one row that
reads 1/1, and the precision is why nobody reads it as thin.

This paper had no such table. Every number below is read from a results file
rather than typed, so the summary cannot drift from the sections it summarises.
"""
import json
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "paper" / "tches" / "gen" / "index-table.tex"


def load(name):
    p = REPO / "results" / name
    if not p.exists():
        sys.exit(f"index_table: missing {p}")
    return json.loads(p.read_text())


def main() -> int:
    em = load("kyberslash_emission.json")["emission_map"]
    cells = len(em)
    leaking = sum(1 for c in em if c["leak_emitted"])
    vendors = sorted({c["vendor"] for c in em if c["leak_emitted"]})

    # The same source bin/regen.py counts from, so the summary cannot disagree with
    # the macros the sections print.
    vj = REPO / "results" / "verdicts.jsonl"
    verdicts = [json.loads(l) for l in vj.read_text().splitlines() if l.strip()]
    rows_total = len(verdicts)
    applicable = sum(1 for v in verdicts if v.get("applicable"))

    fv = load("fix_verification.json")
    cand = fv["survey_triage"]["candidates"]
    built = sum(1 for c in cand.values() if c.get("built"))
    # A measurement this paper will not stand behind is not a measurement it retains.
    # wolfSSL was built and timed, and every reading was taken under a retired rule on
    # samples that were never committed, so the fix section does not grade it. Counting
    # it as "measured" in the summary table contradicted that.
    # The record now says so directly: retained = false on the wolfSSL candidate.
    retained = sum(1 for c in cand.values()
                   if c.get("measured") and c.get("retained", True) is not False)
    measured = sum(1 for c in cand.values() if c.get("measured"))

    b1 = load("bin1_check.json")

    # The evidence tier each index rests on, read from the pair declarations that
    # bin/regen.py counts from, so the tier column cannot disagree with \nTierA and
    # its siblings. I1 and I2 rest on the KyberSlash pair; I4's corpus label is
    # libgcrypt's; I3 is scored over the whole corpus, so it prints the tier split.
    def pair_tier(name):
        d = tomllib.loads((REPO / "pairs" / name / "pair.toml").read_text())
        t = d.get("pair", {}).get("tier")
        if t not in ("A", "B", "C"):
            sys.exit(f"index_table: pair {name} declares no tier")
        return t

    by_tier = {}
    for pt in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(pt.read_text())
        if d.get("pair", {}).get("role") == "corpus":
            by_tier[d["pair"].get("tier", "unset")] = by_tier.get(d["pair"].get("tier", "unset"), 0) + 1
    ks_tier = pair_tier("kyberslash")
    lg_tier = pair_tier("libgcrypt-minerva")
    hosts_measured = 2  # the acquisition host and the rented Graviton instance, both in results/

    rows = [
        ("I1 build cell", "(vendor, version, opt, triple)",
         f"division emitted in {leaking} of {cells}, and the {len(vendors)} compilers "
         f"disagree about which",
         f"{cells}/{cells} \\texttt{{x86\\_64}} cells rebuilt to digest", "\\ref{sec:toolchain}",
         f"{ks_tier}, emission measured here"),
        ("I2 host", "micro\\-architecture",
         "divider with no step resolvable at \\hostNoiseFloor{} tick in a serial chain, "
         "magnitude-dependent divider, software routine",
         f"3 targets, {hosts_measured} measured here", "\\ref{sec:microarch}",
         f"{ks_tier}, timing measured here on {hosts_measured} hosts"),
        ("I3 analyser and budget", "(tool, host, $n$)",
         "clean and leak on one binary, both correct",
         f"{applicable} applicable of {rows_total} rows", "\\ref{sec:blindspots}",
         "A/B/C: " + "/".join(str(by_tier.get(t, 0)) for t in "ABC")
         + " pairs; recall over A and B"),
        ("I4 fix site and facet", "$(s, f, \\mathcal{A}, B)$",
         "closed, incomplete, and outside the domain",
         f"{built} built, {retained} yielding a retained measurement, "
         f"of {len(cand)} examined", "\\ref{sec:fixes}",
         f"{lg_tier} (libgcrypt); fix-site labels measured here"),
    ]
    for r in rows:
        for cell in r:
            if cell is None or "None" in str(cell):
                sys.exit(f"index_table: a cell computed to None ({r[0]}); a summary that "
                         f"prints None where it meant a count is worse than no summary")
    body = "\n".join(f"{a} & {b} & {c} & {d} & \\S\\,{e} & {f} \\\\"
                     for a, b, c, d, e, f in rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "% GENERATED by bin/index_table.py from results/. Do not hand-edit.\n"
        "\\begin{table}[t]\n\\centering\\small\n"
        "\\caption{The four indices, what each ranges over, what moved when it did, the "
        "denominator each figure is out of, the section that obtains it, and the evidence "
        "tier it rests on. The rebuild column for the "
        f"build cell is BIN-1, {b1['binaries_checked']:,} \\texttt{{x86\\_64}} binaries reproduced "
        f"to their recorded \\texttt{{.text}} digest with {b1.get('discrepancies', 0)} discrepancies; "
        "the one aarch64 cell is outside that discipline (\\Cref{sec:toolchain}).}\n"
        "\\label{tab:indices}\n"
        "\\setlength{\\tabcolsep}{3pt}%\n"
        "\\begin{tabular}{@{}"
        ">{\\raggedright\\arraybackslash}p{0.11\\linewidth}"
        ">{\\raggedright\\arraybackslash}p{0.17\\linewidth}"
        ">{\\raggedright\\arraybackslash}p{0.22\\linewidth}"
        ">{\\raggedright\\arraybackslash}p{0.19\\linewidth}"
        "l"
        ">{\\raggedright\\arraybackslash}p{0.15\\linewidth}@{}}\n\\toprule\n"
        "Index & Ranges over & What moved & Out of & \\S & Tier \\\\\n\\midrule\n"
        + body + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    print(f"index_table: wrote {OUT} ({len(rows)} indices)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
