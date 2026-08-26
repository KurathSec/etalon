#!/usr/bin/env python3
"""Emit the field-wide analyser classification table.

The paper scores four analysers. A referee's first question is why four, and the
answer is only credible if the field they were drawn from is on the page. This is
the device Geimer et al. use at CCS: classify the field, then benchmark a subset,
and the classification is what earns the right to the subset.

The row set is a COMPUTATION, not a list we assembled. It is a third-party
inventory taken at a pinned commit and filtered by two predicates that inventory
publishes about itself, plus the analysers this paper scores that it does not
carry. We contribute no rows to it and did not survey the field. That matters
because this paper is not a systematisation and must not read as one.

Two columns are ours. The mechanism block asks whether a tool's own description
states that it reports a secret-dependent branch, a secret-dependent address, or
a variable-latency instruction on secret operands; Geimer folds all three into one
policy column, and splitting them is what makes the KyberSlash class visible as a
hole in the field rather than a hole in one tool. The budget column is the index a
clean verdict is conditional on, which nobody publishes, so it is derived from
technique by a stated rule and marked as derived.

Deliberately absent: a scalability column. Geimer carries one and calls it "a
rough estimation ... based on the claims made in the tools' publications", with a
Limitation paragraph on why it cannot be quantified. Inheriting a column its own
authors disown is exactly the unindexed number this paper argues against.
"""
import argparse
import json
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent
INV = REPO / "data" / "inventories" / "cttools.jsonl"
OVR = REPO / "data" / "analysers.toml"
TOOLS = REPO / "data" / "tools.toml"
OUT = REPO / "paper" / "tches" / "gen" / "analyser-table.tex"
JSON_OUT = REPO / "results" / "analyser_matrix.json"

LEVEL = {"C": "S", "LLVM IR": "I", "Binary": "B", "Trace": "T", "x86": "B"}
BUDGET = {"Statistical": "$n$", "Dynamic": "cov", "Symbolic": "path", "Formal": "--"}
SOUND = {"sound": "\\Sfull", "sound with restrictions": "\\Spart",
         "no": "\\Snone", "other": "\\Sother"}
GLYPH = {"yes": "\\Yes", "no": "\\Not", "unstated": ""}
# The four scored tools, keyed to data/tools.toml so the star column cannot drift
# from the tools the scorer actually runs.
SCORED_KEY = {"dudect": "dudect", "timecop": "timecop", "binsec": "binsec",
              "varlat": "varlat"}
# Only Microwalk has an adapter here (src/corpus/score/adapters/microwalk.py) and
# only its pipeline is recorded as validated end to end. DATA is cited as a family
# member and carries no adapter, so it must not wear the adapter glyph.
ADAPTER = {"microwalk"}
# Inventory slug to the key refs.bib actually uses.
CITE_KEY = {"dudect": "dudect", "timecop": "timecop", "binsec": "binsecrel",
            "ctgrind": "ctgrind", "data": "data", "microwalk": "microwalk",
            "ct-verif": "ctverif", "varlat": "kyberslash", "scoutct": "scoutct"}


def esc(s):
    for a, b in (("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")):
        s = s.replace(a, b)
    return s


def build():
    rows = [json.loads(l) for l in INV.read_text().splitlines()
            if l.strip() and not l.startswith('{"_')]
    ovr = tomllib.loads(OVR.read_text())
    meta, mech = ovr["meta"], ovr.get("mech", {})

    eligible = [r for r in rows if r["target"] in set(meta["target_eligible"])]
    kept = [r for r in eligible if r["available"]] if meta["require_available"] else eligible
    for slug, a in ovr.get("analyser", {}).items():
        kept.append({"slug": slug, "title": a["title"], "year": a.get("year"),
                     "target": a["target"], "technique": a["technique"],
                     "guarantees": a["guarantees"], "available": True,
                     "url": a.get("url", ""), "papers": [], "_added": True})
    # The inventory does not type its year field consistently: one record carries a
    # string. Coerce rather than crash, and keep an unparseable year as unstated.
    for r in kept:
        try:
            r["year"] = int(str(r["year"]).strip()[:4])
        except (TypeError, ValueError):
            r["year"] = None
    kept.sort(key=lambda r: (r["year"] or 9999, r["title"].lower()))

    for r in kept:
        m = mech.get(r["slug"], {})
        r["branch"] = m.get("branch", "unstated")
        r["address"] = m.get("address", "unstated")
        r["varlat"] = m.get("varlat", "unstated")
        r["budget"] = BUDGET.get(r["technique"], "--")
        r["budget_corroborated"] = bool(m.get("budget_corroborated"))
        r["role"] = ("scored" if r["slug"] in SCORED_KEY
                     else "adapter" if r["slug"] in ADAPTER else "")
    return rows, eligible, kept, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    rows, eligible, kept, meta = build()
    scored = [r for r in kept if r["role"] == "scored"]

    # MTX-1: the starred rows are exactly the tools the scorer runs.
    declared = set(tomllib.loads(TOOLS.read_text())["tool"])
    starred = {SCORED_KEY[r["slug"]] for r in scored}
    if starred != declared:
        sys.exit(f"analyser_table: starred {sorted(starred)} but data/tools.toml declares "
                 f"{sorted(declared)}; 'we score four of these' cannot drift from the four "
                 f"the scorer actually runs")

    # MTX-2: a scored row's mechanism cells must equal what the scorer applies.
    tools = tomllib.loads(TOOLS.read_text())["tool"]
    MAP = {"secret-branch": "branch", "address-data": "address",
           "address-code": "address", "variable-latency-op": "varlat"}
    for r in scored:
        want = set()
        for m in tools[SCORED_KEY[r["slug"]]]["detects_mechanisms"]:
            want.add(MAP[m])
        got = {k for k in ("branch", "address", "varlat") if r[k] == "yes"}
        if got != want:
            sys.exit(f"analyser_table: {r['slug']} declares {sorted(want)} in "
                     f"data/tools.toml but the matrix says {sorted(got)}; the matrix would "
                     f"disagree with the applicability lattice that decides every score")

    # MTX-7: a column with no populated cell is refused rather than printed empty.
    for col in ("branch", "address", "varlat"):
        if not any(r[col] != "unstated" for r in kept):
            sys.exit(f"analyser_table: column {col} has no populated cell")

    n_varlat_stated = sum(1 for r in kept if r["varlat"] != "unstated")
    doc = {
        "finding": "the field this paper's four analysers were drawn from",
        "why": ("The row set is a pinned third-party inventory filtered by two predicates "
                "it publishes about itself, plus the analysers scored here that it does "
                "not carry. We contribute no rows and did not survey the field."),
        "generator": "bin/analyser_table.py",
        "inventory_commit": json.loads(INV.read_text().splitlines()[0])["_commit"],
        "indexed": len(rows),
        "target_eligible": len(eligible),
        "classified": len(kept),
        "added_by_us": sum(1 for r in kept if r.get("_added")),
        "scored": len(scored),
        "varlat_stated": n_varlat_stated,
        "varlat_unstated": len(kept) - n_varlat_stated,
        "budget_corroborated": sum(1 for r in kept if r["budget_corroborated"]),
        "dropped_target": sorted(r["title"] for r in rows if r not in eligible),
        "dropped_unavailable": sorted(r["title"] for r in eligible if not r["available"]),
    }

    if args.check:
        if not JSON_OUT.exists():
            print("analyser_table: results/analyser_matrix.json missing", file=sys.stderr)
            return 1
        old = json.loads(JSON_OUT.read_text())
        bad = [k for k in ("indexed", "classified", "scored", "varlat_unstated")
               if old.get(k) != doc[k]]
        if bad:
            print(f"analyser_table: {', '.join(bad)} differ from committed", file=sys.stderr)
            return 1
        print(f"analyser_table: check clean ({doc['classified']} classified)")
        return 0

    body = []
    for r in kept:
        # Cite only where refs.bib carries an entry, and under the key it uses: the
        # inventory's slug is not a bibliography key. A wrong key renders as [?] and
        # LaTeX reports it as an undefined CITATION, which is a different warning from
        # an undefined reference and was not being gated.
        key = CITE_KEY.get(r["slug"])
        cite = f"~\\cite{{{key}}}" if key else ""
        star = {"scored": "\\Scored", "adapter": "\\Adapter", "": ""}[r["role"]]
        bud = r["budget"] + ("\\textsuperscript{\\ddag}" if r["budget_corroborated"] else "")
        body.append(
            f"{esc(r['title'])}{cite} & {r['year'] or '--'} & {LEVEL.get(r['target'], '?')} & "
            f"{r['technique'].lower()} & {GLYPH[r['branch']]} & {GLYPH[r['address']]} & "
            f"{GLYPH[r['varlat']]} & {bud} & {SOUND.get(r['guarantees'], '')} & {star} \\\\")

    JSON_OUT.write_text(json.dumps(doc, indent=1) + "\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "% GENERATED by bin/analyser_table.py from data/inventories/ and data/analysers.toml.\n"
        "% Do not hand-edit.\n"
        "\\begin{table}[!t]\n\\centering\\footnotesize\n\\renewcommand{\\arraystretch}{0.94}\n"
        f"\\caption{{The field the \\nToolsWord{{}} scored analysers were drawn from. The rows are "
        f"not ours: they are the \\nFieldIndexed{{}} tools of a third-party "
        f"inventory~\\cite{{cttools}} at a pinned commit, filtered by two predicates that "
        f"inventory publishes about itself, leaving \\nFieldAvailEligible{{}}, plus the "
        f"\\nFieldAddedWord{{}} scored here that it does not carry. We contribute no rows and "
        f"did not survey the field. A blank under \\textbf{{Detects}} is an absence rather "
        f"than a denial. \\Yes{{}} declared, \\Not{{}} declared not covered; \\ddag{{}} the "
        f"budget cell is corroborated by the tool's own documentation; \\Sfull{{}} sound, "
        f"\\Spart{{}} sound with restrictions, \\Snone{{}} no guarantee, \\Sother{{}} "
        f"guarantees a different property; \\Scored{{}} scored here, \\Adapter{{}} adapter "
        f"built but not scored per pair.}}\n"
        "\\label{tab:analysers}\n\\setlength{\\tabcolsep}{3pt}\n"
        "\\begin{tabular}{@{}lrclcccllc@{}}\n\\toprule\n"
        " & & & & \\multicolumn{3}{c}{Detects} & & & \\\\\n\\cmidrule(lr){5-7}\n"
        "Tool & Yr & Lvl & Method & b & a & v & Bud & Snd & \\\\\n\\midrule\n"
        + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    print(f"analyser_table: wrote {OUT} ({doc['classified']} classified, "
          f"{doc['scored']} scored, {doc['varlat_unstated']} varlat cells unstated)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
