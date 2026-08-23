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
                out.append(tex_macro(name + "WordCap", WORDS[value].capitalize()))
        elif hasattr(value, "defined"):
            # A rate carries its n, and an undefined one is NA and never 0.
            if value.defined:
                out.append(tex_macro(name, f"{value.value * 100:.1f}\\%"))
            else:
                out.append(tex_macro(name, "\\NA"))
            emit(name + "N", value.n)
        else:
            out.append(tex_macro(name, str(value)))

    # Analysers actually registered and scored (data/tools.toml).
    tp = REPO / "data" / "tools.toml"
    if tp.exists():
        emit("nTools", len(tomllib.loads(tp.read_text()).get("tool", {})))

    c = report["corpus"]
    emit("nPairs", c["pairs_total"])
    emit("nPairsCorpus", c["pairs_corpus"])
    emit("nPairsSentinel", c["pairs_sentinel"])
    emit("nRecallEligible", c["recall_eligible_pairs"])

    cen = report["census"]
    emit("nCensusEntries", cen["census_entries"])
    emit("nAttestedCells", cen["attested_cells"])
    emit("coverage", cen["covered_cells"])
    # The coverage numerator as its own macro, so "six of eleven" is generated
    # rather than the six being retyped beside the generated eleven.
    emit("nCoveredCells", cen["covered_cells"].numerator)
    emit("nUncoveredCells", len(cen["uncovered_cells"]))

    v = report["verdicts"]
    emit("nScoredRows", v["scored_rows"])
    emit("nApplicable", v["applicable"])
    emit("nInapplicable", v["inapplicable"])
    # Detected and missed are real counts when applicable rows exist, and NA when
    # none do. A default 0 over an empty applicable set is exactly the mean([])
    # defect this module refuses: it would read as "measured, found nothing".
    outs = v.get("outcomes")
    has_applicable = isinstance(outs, dict)
    emit("nDetected", outs.get("detected", 0) if has_applicable else None)
    emit("nMissed", outs.get("missed", 0) if has_applicable else None)

    co = report["cost"]
    emit("nCostRows", co["cost_rows"])

    # Per-class recall, from the recorded scoring run. These are the numbers the
    # project exists to produce. They render as real fractions, not NA, once a
    # scoring run exists; the HEADLINE gate is separate and still governs whether
    # an aggregate recall figure may be stated.
    rp = REPO / "results" / "recall.json"
    recall_doc = json.loads(rp.read_text()) if rp.exists() else {}
    for r in recall_doc.get("recall_per_class", []):
        tool = r["tool"]
        obs = "Latency" if "observable=latency" in r["class"] else "Address" if "observable=address-data" in r["class"] else ""
        if obs:
            out.append(tex_macro(f"recall{tool.capitalize()}{obs}",
                                 r["recall"].replace("/", "\\,of\\,")))
    # tier-C detection outcomes (the crossover), per pair and tool, so the paper
    # can name e.g. dudect missed while varlat and binsec detected KyberSlash.
    outcome_word = {"detected": "detected", "missed": "missed",
                    "non_discriminating": "non-discriminating",
                    "budget_exhausted": "inconclusive", "error": "errored"}
    for r in recall_doc.get("tier_c_detections", []):
        pair_key = "".join(ch for ch in r["pair"] if ch.isalpha())
        out.append(tex_macro(f"{pair_key}{r['tool'].capitalize()}",
                             outcome_word.get(r["outcome"], r["outcome"])))

    # The KyberSlash microarchitecture finding, measured on rented Graviton3 and
    # committed at results/kyberslash_graviton.json. These are acquired
    # observations, regenerable only on an aarch64 host, echoed here so the paper
    # quotes no hand-typed measurement. Point measurements, so no n travels.
    gp = REPO / "results" / "kyberslash_graviton.json"
    if gp.exists():
        g = json.loads(gp.read_text())
        step = g["results"]["kyberslash_operand_range_step"]
        e2e = g["results"]["end_to_end_coeff_to_bit_Os"]
        codegen = g["results"]["codegen"]["udiv_in_coeff_to_bit"]
        snr = int(round(step["step_ticks"] / step["noise_floor_ticks"], -2))
        out.append(tex_macro("gravHost", "AWS Graviton3 (Neoverse\\,V1)"))
        out.append(tex_macro("gravOsUdiv", str(codegen["Os"])))
        out.append(tex_macro("gravStepTicks", f"{step['step_ticks']:.3f}"))
        out.append(tex_macro("gravSNR", str(snr)))
        out.append(tex_macro("gravDeltaTicks", f"{e2e['secret_dependent_delta_ticks']:.3f}"))
        out.append(tex_macro("gravDeltaPercent", f"{e2e['delta_percent_of_call']:.1f}\\%"))

    # Fuller detail for the expanded design and results sections.
    sp = REPO / "results" / "scoring.json"
    if sp.exists():
        cpu = json.loads(sp.read_text()).get("measured_on", "").split(",")[0].strip()
        if cpu:
            out.append(tex_macro("acqHost", cpu))
    for r in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if (r.get("tool") == "dudect" and r.get("pair") == "kyberslash"
                and r.get("patched_max_t") is not None):
            out.append(tex_macro("tDudectDivisionPatched", f"{r['patched_max_t']:.2f}"))
    for t in ("A", "B", "C"):
        emit(f"nTier{t}", report["corpus"]["by_tier"].get(t, 0))
    emit("nCensusIncluded", cen["census_included"])
    emit("nCensusExcluded", cen["census_excluded"])
    for macro, key in (("portableHours", "portable_hours_mean"),
                       ("acquisitionHours", "acquisition_hours_mean")):
        m = report["cost"][key]
        out.append(tex_macro(macro, f"{m.value:.1f}" if m.defined else "\\NA"))
        emit(macro + "N", m.n)
    # dudect's t-statistic, the statistical tool's stopping value on the
    # vulnerable arm: huge on the nonce leaks, ~2 on the division it misses.
    t_named = {"ecdsa-nonce": "tDudectNonceLatency",
               "ecdsa-address": "tDudectNonceAddress",
               "kyberslash": "tDudectDivision",
               "hqc-reject": "tDudectRejection",
               "_sentinel-positive": "tSentinelPos"}
    for r in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if r.get("tool") == "dudect" and r.get("applicable") and r["pair"] in t_named:
            v = r.get("vulnerable_max_t")
            if v is not None:
                out.append(tex_macro(t_named[r["pair"]],
                                     f"{v:.0f}" if v >= 10 else f"{v:.2f}"))
    # KyberSlash emission map: cells built, and how many emit the division.
    ep = REPO / "results" / "kyberslash_emission.json"
    if ep.exists():
        cells = json.loads(ep.read_text()).get("emission_map", [])
        leaking = sum(1 for c in cells if c.get("leak_emitted"))
        emit("nEmissionCells", len(cells))
        emit("nLeakingCells", leaking)
        emit("nConstantTimeCells", len(cells) - leaking)

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
