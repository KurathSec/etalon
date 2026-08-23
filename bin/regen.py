#!/usr/bin/env python3
"""Regenerate every number this project would quote, each beside its n.

A number does not exist until a committed script regenerates it from committed
data. This is that script, and it is written before there is any data, because
adding it afterwards means the first numbers were prose.

Two rules it enforces mechanically rather than by convention:

  * An aggregation over nothing prints NA, never 0. A reported 0.00 that was
    mean([]) and a reported 0.946 that was the identity (s - c) / (s - c) are
    both real, both were caught late, and both read as findings.

  * `--headline` refuses to print a recall figure unless the coverage line and
    the named uncovered cells print in the same output. Recall over a corpus is
    a lower bound on the classes the corpus contains, so a recall figure quoted
    without its coverage is not a weaker claim, it is a different and false one.
    The programme has already been burned once by a coverage fraction whose
    denominator turned out to be underivable, and the defence is that the tool
    will not emit the numerator alone.

Usage:  bin/regen.py [--json] [--headline]

Exit codes: 0 printed, 1 refused (a gate fired), 2 could not run.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from corpus.util.na import NA, Rate, mean  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def corpus_section() -> dict:
    pairs = sorted((REPO / "pairs").glob("*/pair.toml"))
    loaded = [(p.parent.name, tomllib.loads(p.read_text())) for p in pairs]
    corpus = [(n, d) for n, d in loaded if d.get("pair", {}).get("role") == "corpus"]
    sentinels = [(n, d) for n, d in loaded if n.startswith("_sentinel")]

    tiers = {}
    for name, d in corpus:
        tiers.setdefault(d.get("pair", {}).get("tier", "unset"), []).append(name)

    eligible = len(tiers.get("A", [])) + len(tiers.get("B", []))
    return {
        "pairs_total": len(loaded),
        "pairs_corpus": len(corpus),
        "pairs_sentinel": len(sentinels),
        "by_tier": {k: len(v) for k, v in sorted(tiers.items())},
        # Tier C is listed and never counted. This is the denominator that
        # decides whether there is a measured recall to report at all.
        "recall_eligible_pairs": eligible,
        "recall_eligible_names": sorted(
            tiers.get("A", []) + tiers.get("B", [])),
    }


def census_section() -> dict:
    rows = read_jsonl(REPO / "data" / "census" / "entries.jsonl")
    meta_path = REPO / "data" / "census" / "META.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    # Only adjudicated-in rows are attested. An excluded row is evidence that
    # the class was considered and ruled out of scope, and counting it would
    # inflate the denominator with something the corpus never intended to cover.
    included = [r for r in rows
                if r.get("adjudication") == "included" and r.get("facets")]
    attested = {tuple(sorted(r["facets"].items())) for r in included}
    covered = set()
    for p in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(p.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        cls = d.get("class", {})
        facets = {k: v for k, v in cls.items() if k not in ("rationale", "mechanism_classes")}
        if facets:
            covered.add(tuple(sorted(facets.items())))
    uncovered = attested - covered
    return {
        # census_status travels with the number, because a seed census makes
        # coverage look better than it is.
        "census_status": meta.get("census_status", "UNDECLARED"),
        "census_entries": len(rows),
        "census_included": len(included),
        "census_excluded": len(rows) - len(included),
        "attested_cells": len(attested),
        "covered_cells": Rate(len(attested & covered), len(attested),
                              "coverage of attested leak-class cells"),
        "uncovered_cells": sorted(
            "/".join(f"{k}={v}" for k, v in cell) for cell in uncovered),
    }


def verdict_section() -> dict:
    rows = read_jsonl(REPO / "results" / "verdicts.jsonl")
    applicable = [r for r in rows if r.get("applicable")]
    inapplicable = [r for r in rows if r.get("applicable") is False]
    outcomes = {}
    for r in applicable:
        o = r.get("outcome", "unset")
        outcomes[o] = outcomes.get(o, 0) + 1
    return {"scored_rows": len(rows),
            "applicable": len(applicable),
            "inapplicable": len(inapplicable),
            "outcomes": outcomes if outcomes else NA}


def cost_section() -> dict:
    # KT3 lives in each pair's manifest [cost] block, not a separate ledger, so
    # it cannot be forgotten when a pair is added. Only corpus pairs are priced;
    # fixtures price the format, not a corpus item.
    portable, acq = [], []
    for path in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(path.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        cost = d.get("cost", {})
        if "portable_hours" in cost:
            portable.append(cost["portable_hours"])
        if "acquisition_hours" in cost:
            acq.append(cost["acquisition_hours"])
    rows = portable
    # Two clocks, never summed. A single per-pair figure mixes an effort that
    # runs anywhere with one bounded by hardware, and is not measurable.
    return {"cost_rows": len(rows),
            "portable_hours_mean": mean(portable, "portable effort per pair"),
            "acquisition_hours_mean": mean(acq, "acquisition effort per pair")}


def render(value) -> str:
    # Rate.render() and Mean.render() already carry their own n, so appending
    # another one here printed it twice.
    if hasattr(value, "render") and hasattr(value, "n"):
        return value.render()
    if isinstance(value, list):
        return f"[{len(value)}] " + (", ".join(map(str, value)) if value else NA)
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}={v}" for k, v in value.items()) + "}" if value else NA
    return str(value)


TEX_HEADER = r"""% GENERATED by bin/regen.py. Do not hand-edit.
%
% Every number the paper quotes is a macro defined here, and every macro is
% derived from committed data. A number typed directly into the body is a number
% nobody can re-derive, which is how a prior result in this programme survived
% only as prose.
%
% Absent quantities expand to \NA, never to 0. A macro that renders as NA in the
% built PDF is the gate working: it means the claim it supports has no data yet,
% and it is visible in the draft rather than silently plausible.
%
% Counts are emitted twice, as digits and as words, so a sentence can spell a
% small number without anyone retyping it.

\providecommand{\NA}{\textsc{na}}
"""

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve"]


def tex_macro(name: str, body: str) -> str:
    return "\\newcommand{\\%s}{%s}\n" % (name, body)


def as_tex(report: dict) -> str:
    """Render the report as macros. Digits and words for counts, NA for absent."""
    out = [TEX_HEADER, ""]

    def emit(name: str, value):
        if value is None:
            out.append(tex_macro(name, "\\NA"))
        elif isinstance(value, int):
            out.append(tex_macro(name, str(value)))
            if 0 <= value < len(WORDS):
                out.append(tex_macro(name + "Word", WORDS[value]))
        elif hasattr(value, "defined"):
            # A rate carries its n, and an undefined one is NA and never 0.
            if value.defined:
                out.append(tex_macro(name, f"{value.value * 100:.1f}\\%"))
            else:
                out.append(tex_macro(name, "\\NA"))
            emit(name + "N", value.n)
        else:
            out.append(tex_macro(name, str(value)))

    c = report["corpus"]
    emit("nPairs", c["pairs_total"])
    emit("nPairsCorpus", c["pairs_corpus"])
    emit("nPairsSentinel", c["pairs_sentinel"])
    emit("nRecallEligible", c["recall_eligible_pairs"])

    cen = report["census"]
    emit("nCensusEntries", cen["census_entries"])
    emit("nAttestedCells", cen["attested_cells"])
    emit("coverage", cen["covered_cells"])
    emit("nUncoveredCells", len(cen["uncovered_cells"]))

    v = report["verdicts"]
    emit("nScoredRows", v["scored_rows"])
    emit("nApplicable", v["applicable"])
    emit("nInapplicable", v["inapplicable"])
    outs = v.get("outcomes") or {}
    if isinstance(outs, dict):
        emit("nDetected", outs.get("detected", 0))
        emit("nMissed", outs.get("missed", 0))

    co = report["cost"]
    emit("nCostRows", co["cost_rows"])

    # Per-class recall, from the recorded scoring run. These are the numbers the
    # project exists to produce. They render as real fractions, not NA, once a
    # scoring run exists; the HEADLINE gate is separate and still governs whether
    # an aggregate recall figure may be stated.
    import json as _json
    rp = REPO / "results" / "recall.json"
    if rp.exists():
        rec = _json.loads(rp.read_text()).get("recall_per_class", [])
        for r in rec:
            tool = r["tool"]
            obs = "Latency" if "observable=latency" in r["class"] else "Address" if "observable=address-data" in r["class"] else ""
            if obs:
                out.append(tex_macro(f"recall{tool.capitalize()}{obs}",
                                     r["recall"].replace("/", "\\,of\\,")))
    # tier-C detection outcomes (the crossover): dudect miss / varlat catch
    tc = _json.loads(rp.read_text()).get("tier_c_detections", []) if rp.exists() else []
    for r in tc:
        if r["pair"] == "kyberslash":
            out.append(tex_macro(f"kyberslash{r['tool'].capitalize()}",
                                 "detected" if r["outcome"]=="detected" else "missed"))

    # Facts about the field, not about this corpus. They are still generated,
    # because a hand-typed 55 is a number nobody can re-derive either.
    facts = tomllib.loads((REPO / "data" / "facts.toml").read_text()) \
        if (REPO / "data" / "facts.toml").exists() else {}
    for key, entry in sorted(facts.get("fact", {}).items()):
        emit(key, entry["value"])
        out.append("%% %s: %s\n" % (key, entry["source"]))

    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--headline", action="store_true",
                    help="print the recall figure; refuses unless coverage prints with it")
    ap.add_argument("--tex", metavar="PATH",
                    help="write every quotable number as a LaTeX macro")
    args = ap.parse_args()

    report = {
        "corpus": corpus_section(),
        "census": census_section(),
        "verdicts": verdict_section(),
        "cost": cost_section(),
    }

    if args.json:
        def enc(o):
            if hasattr(o, "as_record"):
                return o.as_record()
            raise TypeError(type(o))
        print(json.dumps(report, indent=2, default=enc))
    else:
        for section, body in report.items():
            print(f"\n[{section}]")
            for k, v in body.items():
                print(f"  {k:<26} {render(v)}")

    if args.tex:
        out = Path(args.tex)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(as_tex(report), encoding="utf-8")
        print(f"regen: wrote {out}")

    if args.headline:
        print()
        eligible = report["corpus"]["recall_eligible_pairs"]
        coverage = report["census"]["covered_cells"]
        reasons = []
        if eligible < 4:
            reasons.append(
                f"KT6: only {eligible} pair(s) are tier A or B, and the threshold "
                f"fixed in advance is 4. Tier C items never enter a denominator, "
                f"so there is no measured recall to report")
        if not coverage.defined:
            reasons.append(
                "CLS-3: the census is empty, so coverage of the leak-class space "
                "has no denominator and a recall figure cannot be placed in context")
        elif report["census"]["census_status"] != "complete":
            reasons.append(
                f"CLS-3: the census is declared '{report['census']['census_status']}', "
                f"not complete, so the coverage denominator is provisional and a "
                f"headline recall figure would overstate what the corpus covers")
        if reasons:
            print("regen: REFUSING to print a headline recall figure.")
            for r in reasons:
                print(f"  - {r}")
            print("\n  This refusal is the gate working, not a bug.")
            return 1
        print(f"recall headline permitted: coverage {coverage.render()} "
              f"(n={coverage.n}), uncovered cells listed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
