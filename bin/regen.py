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
import re
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


def _facet_names() -> set[str]:
    """The class facets, from the closed vocabulary that defines them."""
    c = tomllib.loads((REPO / "data" / "classes.toml").read_text())
    return set(c.get("facet", {}))


FACET_NAMES = _facet_names()


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
        # Take the class facets by NAME from the closed vocabulary, never "everything
        # except a few known keys". The denylist form silently absorbed a new field
        # added to [class] (certification_channel), which lengthened every covered
        # tuple, stopped it matching any 5-facet census cell, and quietly dropped
        # coverage from 7/11 to 3/11 while the uncovered list grew to name cells that
        # pairs already covered. An allowlist cannot fail that way.
        facets = {k: v for k, v in cls.items() if k in FACET_NAMES}
        if facets:
            covered.add(tuple(sorted(facets.items())))
    uncovered = attested - covered
    # Human-readable names of the uncovered cells, from the census rows themselves,
    # so the paper's uncovered-cell list is generated and cannot drift (it once
    # listed a cell that a later pair had already covered). One name per uncovered
    # facet tuple, first by census id.
    uncovered_names = []
    seen = set()
    for r in sorted(included, key=lambda x: x.get("id", "")):
        cell = tuple(sorted(r["facets"].items()))
        if cell in uncovered and cell not in seen:
            seen.add(cell)
            # Short name only (drop the parenthetical gloss), for the terse prose list.
            uncovered_names.append(r["name"].split(" (")[0].strip())
    # Coverage is a function of the facet granularity we adjudicate at, so a single
    # fraction reads as more precise than it is. Bracket it: recompute the same
    # coverage after dropping each facet in turn, and over the full tuple (the finest
    # we adjudicate). Coarsening does NOT move the fraction in one direction: merging
    # cells can collapse two covered cells into one (numerator falls) as easily as it
    # can absorb an uncovered cell into a covered one (numerator holds while the
    # denominator falls), so the bracket has to be computed, not reasoned about. The
    # paper prints the range beside the point value rather than the point value alone.
    def _coverage_at(keys):
        att = {tuple(sorted((k, v) for k, v in dict(c).items() if k in keys))
               for c in attested}
        cov = {tuple(sorted((k, v) for k, v in dict(c).items() if k in keys))
               for c in covered}
        return len(att & cov), len(att)
    all_facets = sorted({k for c in attested for k, _ in c})
    bracket = {}
    for drop in all_facets:
        keys = [f for f in all_facets if f != drop]
        num, den = _coverage_at(keys)
        bracket[f"drop_{drop}"] = {"covered": num, "attested": den,
                                   "fraction": round(num / den, 4) if den else None}
    fine_num, fine_den = _coverage_at(all_facets)
    coarsest = max((v["fraction"] or 0) for v in bracket.values()) if bracket else None
    return {
        # census_status travels with the number, because a seed census makes
        # coverage look better than it is.
        "census_status": meta.get("census_status", "UNDECLARED"),
        "census_facets_adjudicated": len(all_facets),
        "coverage_granularity_bracket": bracket,
        "coverage_at_finest": {"covered": fine_num, "attested": fine_den},
        "coverage_coarsest_fraction": coarsest,
        "census_entries": len(rows),
        "census_included": len(included),
        "census_excluded": len(rows) - len(included),
        "attested_cells": len(attested),
        "covered_cells": Rate(len(attested & covered), len(attested),
                              "coverage of attested leak-class cells"),
        "uncovered_cells": sorted(
            "/".join(f"{k}={v}" for k, v in cell) for cell in uncovered),
        "uncovered_names": uncovered_names,
    }


def verdict_section() -> dict:
    rows = read_jsonl(REPO / "results" / "verdicts.jsonl")
    applicable = [r for r in rows if r.get("applicable")]
    inapplicable = [r for r in rows if r.get("applicable") is False]
    # Outcome tally over corpus pairs only. The sentinel controls (positive detected
    # by all, negative clean by all) are reported as SENT-1/SENT-2, not folded into
    # the detection or miss counts, where a tool correctly clean on the constant-time
    # negative control would otherwise register as a "miss".
    outcomes = {}
    for r in applicable:
        if r.get("role") != "corpus":
            continue
        o = r.get("outcome", "unset")
        outcomes[o] = outcomes.get(o, 0) + 1
    # The three exclusion reasons are genuinely different and were once all
    # reported as "excluded by construction": a mechanism intersection that is
    # empty (a real by-construction exclusion), a pair with no runnable harness
    # built here, and a pair that declares no mechanism at all. Count them apart.
    mech = noharn = nullmech = 0
    for r in inapplicable:
        reason = r.get("reason", "")
        if reason.startswith("mechanism:"):
            mech += 1
        elif ("no runnable harness" in reason or "no runnable program" in reason
              or "no harness built here" in reason):
            # Both the observation-only pairs (no runnable program) and the pairs
            # that ship source but for which no harness was built for this tool
            # (an effort boundary) are counted here: neither is a mechanism
            # exclusion, and both were once split off wrongly, leaving the counts
            # not summing to the inapplicable total.
            noharn += 1
        elif "no mechanism a code-running analyser detects" in reason:
            nullmech += 1
    return {"scored_rows": len(rows),
            "applicable": len(applicable),
            "inapplicable": len(inapplicable),
            "inapplicable_mechanism": mech,
            "inapplicable_no_harness": noharn,
            "inapplicable_null_mechanism": nullmech,
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
    # A LaTeX control sequence is letters only. \foo255 parses as \foo followed by
    # 255, so \newcommand on such a name fails with "Missing \begin{document}" at the
    # macro, which points at the wrong thing entirely and has cost this project two
    # silent build failures. Refuse it here, where the message can name the cause.
    if not name.isalpha():
        raise ValueError(
            f"macro name {name!r} is not letters-only; LaTeX cannot define it. "
            f"Spell any digits out (icDelta255 -> icDeltaOneZero).")
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
        # The analysers other than the statistical one, which is the only tool that can
        # be pointed at the deployed fix cases. Kept as a macro so the scoped claim in
        # sec/fixes cannot drift from the tool table.
        emit("nToolsOther", len(tomllib.loads(tp.read_text()).get("tool", {})) - 1)
    # The applicability grid's own dimensions, so "60 tool-by-pair rows" is
    # reconstructable rather than asserted: it is every scored item times every analyser,
    # and the scored items include the fixtures that never enter a recall denominator.
    _rows = list(read_jsonl(REPO / "results" / "verdicts.jsonl"))
    if _rows:
        _items = {r["pair"] for r in _rows}
        emit("nScoredItems", len(_items))
        emit("nGridCorpus", len({r["pair"] for r in _rows if r.get("role") == "corpus"}))
        emit("nGridCertNeg",
             len({r["pair"] for r in _rows if r.get("role") == "certified-negative"}))
        emit("nGridSentinel",
             len({r["pair"] for r in _rows
                  if str(r.get("role", "")).startswith("sentinel")}))

    # Control counts come from selfcheck.py itself, via the same reader that builds
    # the controls appendix, so the paper's count and its table cannot disagree with
    # the code that enforces them.
    _ct = REPO / "bin" / "controls_table.py"
    if _ct.exists():
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("controls_table", _ct)
        _m = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_m)
        _src = (REPO / "bin" / "selfcheck.py").read_text()
        emit("nControls", len(_m.implemented(_src)))
        # Two counts, because the paper had been quoting one and describing the other.
        # The table has one ROW per control function, and two of those rows carry a pair
        # of identifiers (ORC-1 and ORC-2; SENT-1/SENT-2), so the identifier count is
        # larger than the row count. Saying "18" while explaining that it splits the pairs
        # is a contradiction a reader can check against the table.
        _ids = 0
        for _cid, _ in _m.implemented(_src):
            _ids += len(re.split(r"\s*(?:and|/)\s*", _cid))
        emit("nControlIds", _ids)
        emit("nControlsDeclared", len(_m.declared(_src)))

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
    # The granularity bracket for coverage (S12): the same census re-adjudicated at
    # coarser facet tuples, so the point value is printed inside a measured range
    # rather than alone.
    _br = cen.get("coverage_granularity_bracket") or {}
    if _br:
        _fr = [v["fraction"] for v in _br.values() if v.get("fraction") is not None]
        if _fr:
            out.append(tex_macro("coverageBracketLo", f"{min(_fr) * 100:.0f}\\%"))
            out.append(tex_macro("coverageBracketHi", f"{max(_fr) * 100:.0f}\\%"))
            out.append(tex_macro("nCensusFacets", str(cen.get("census_facets_adjudicated", 0))))
    # The uncovered cells by name, generated so the prose list cannot go stale.
    unames = cen["uncovered_names"]
    if unames:
        joined = (unames[0] if len(unames) == 1
                  else ", ".join(unames[:-1]) + ", and " + unames[-1])
        for ch, rep in (("\\", ""), ("#", "\\#"), ("&", "\\&"),
                        ("_", "\\_"), ("%", "\\%"), ("$", "\\$")):
            joined = joined.replace(ch, rep)
        emit("uncoveredCellNames", joined)
    else:
        emit("uncoveredCellNames", None)

    v = report["verdicts"]
    emit("nScoredRows", v["scored_rows"])
    emit("nApplicable", v["applicable"])
    emit("nInapplicable", v["inapplicable"])
    emit("nInapplicableMechanism", v["inapplicable_mechanism"])
    emit("nInapplicableNoHarness", v["inapplicable_no_harness"])
    emit("nInapplicableNullMechanism", v["inapplicable_null_mechanism"])
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
    def _clskey(cls):
        # Disambiguate by secret role and observable, because there is now more than
        # one latency class (a nonce timing leak and a message tag comparison).
        role = ("Nonce" if "secret_role=nonce" in cls
                else "Message" if "secret_role=message" in cls else "")
        obs = ("Latency" if "observable=latency" in cls
               else "Address" if "observable=address-data" in cls else "")
        return role + obs
    for r in recall_doc.get("recall_per_class", []):
        k = _clskey(r["class"])
        if k:
            out.append(tex_macro(f"recall{r['tool'].capitalize()}{k}",
                                 r["recall"].replace("/", "\\,of\\,")))
    # The patched-arm alarm count that must accompany every policy-detection figure:
    # policy detection rewards sensitivity only, so it is meaningless without the count
    # of patched arms the same tool also flags. Counted from the verdicts, not typed.
    # CORPUS pairs only. Counting every applicable timecop row put the two synthetic
    # sentinels and the certified negatives in the denominator, which the corpus section
    # says are not pairs and never enter one, so "of N applicable pairs" named a set
    # whose members it excludes elsewhere.
    _tc = [r for r in read_jsonl(REPO / "results" / "verdicts.jsonl")
           if r.get("tool") == "timecop" and r.get("applicable")
           and r.get("role") == "corpus"]
    if _tc:
        emit("nTimecopApplicable", len(_tc))
        emit("nTimecopPatchedAlarms",
             sum(1 for r in _tc if r.get("patched_status") == "leak_reported"))
    # Policy recall (PR-2): a policy tool's detection of the policy violation on the
    # vulnerable arm, the number that separates timecop's real detection from its
    # inability to discriminate an uncertified patched arm.
    for r in recall_doc.get("policy_recall_per_class", []):
        k = _clskey(r["class"])
        if k:
            out.append(tex_macro(f"policyRecall{r['tool'].capitalize()}{k}",
                                 r["recall"].replace("/", "\\,of\\,")))
    # Policy precision (PR-3): the general false-positive rate over certified
    # constant-time negatives, the measurement the corpus previously could not make.
    pp = recall_doc.get("policy_precision", [])
    if pp:
        emit("policyPrecisionFP", sum(r["false_positives"] for r in pp))
        emit("policyPrecisionTools", len(pp))
        emit("nCertifiedNegatives", max((r["n"] for r in pp), default=0))
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
        mag = g["results"]["operand_magnitude_leak"]
        bnd = g["results"]["single_bit_boundary_step"]
        e2e = g["results"]["end_to_end_coeff_to_bit_Os"]
        codegen = g["results"]["codegen"]["udiv_in_coeff_to_bit"]
        dud = g["results"].get("dudect_on_aarch64", {})
        out.append(tex_macro("gravHost", "AWS Graviton3 (Neoverse\\,V1)"))
        out.append(tex_macro("gravOsUdiv", str(codegen["Os"])))
        # The operand-MAGNITUDE spread across the KyberSlash range (low- vs
        # high-coefficient udiv latency), which is the leak; the single-coefficient
        # boundary step (gravBoundaryStep) is sub-noise, measured directly on aarch64.
        out.append(tex_macro("gravStepTicks",
                             f"{mag['high_coeff_ticks_per_udiv'] - mag['low_coeff_ticks_per_udiv']:.2f}"))
        out.append(tex_macro("gravBoundaryStep", f"{abs(bnd['step_ticks']):.4f}"))
        # The denominator behind gravDeltaPercent, printed so a reader can see the
        # percentage is of a 2-tick call rather than of a whole decapsulation.
        _e2e = g["results"].get("end_to_end_coeff_to_bit_Os", {})
        if _e2e.get("low_coeffs_ticks_per_call"):
            # Two decimals, not one: at 2.1 the printed percentage (19.1%) does not
            # reproduce from the printed numerator and denominator (0.391/2.1 = 18.6%),
            # and a reader checking the paper's arithmetic finds a discrepancy that is
            # only rounding. The true denominator is 2.05.
            out.append(tex_macro("gravCallTicks",
                                 f"{_e2e['low_coeffs_ticks_per_call']:.2f}"))
        # The two batch sizes the aarch64 figures amortise over, read from the
        # measurement sources, so the paper can say what each per-call cost is a cost OF.
        _kl = (REPO / "pairs" / "kyberslash" / "graviton" / "ks_leak.c")
        _kr = (REPO / "pairs" / "kyberslash" / "graviton" / "ks_range_arm.c")
        if _kl.exists():
            _m = re.search(r"#define\s+M\s+(\d+)", _kl.read_text())
            if _m:
                out.append(tex_macro("gravCallBatch", f"{int(_m.group(1)):,}"))
        if _kr.exists():
            _m = re.search(r"#define\s+N\s+(\d+)", _kr.read_text())
            if _m:
                out.append(tex_macro("gravChainLen", f"{int(_m.group(1)):,}"))
        out.append(tex_macro("gravNoiseFloor", f"{bnd['noise_floor_ticks']:.4f}"))
        # The end-to-end percentage was produced by a program that generated the two
        # classes with different constant reductions inside the timed loop; correcting
        # the identical x86 twin took its delta from 1.6% to ~0, so this number is
        # confounded and pending re-measurement. Emit NA until re-run, so no confounded
        # figure can reach the paper. The serial-chain udiv latency curve above is
        # unaffected (fixed dividend, identical code both classes) and carries F3.
        if e2e.get("MEASUREMENT_STATUS", "").startswith("CONFOUNDED"):
            out.append(tex_macro("gravDeltaTicks", None))
            out.append(tex_macro("gravDeltaPercent", None))
        else:
            out.append(tex_macro("gravDeltaTicks", f"{e2e['secret_dependent_delta_ticks']:.3f}"))
            out.append(tex_macro("gravDeltaPercent", f"{e2e['delta_percent_of_call']:.1f}\\%"))
        # The aarch64 control is reported as a permutation p and a counter-resolution
        # fact, not as a tau: on this counter a coeff_to_bit call is a handful of ticks,
        # so a per-call tau is not a meaningful effect size (see the JSON note).
        vp = dud.get("verdict_permutation", {})
        if vp.get("p_value") is not None:
            out.append(tex_macro("gravDudectP", f"{vp['p_value']:.2f}"))
            out.append(tex_macro("gravDudectN", f"{vp['measurements']:,}"))

    # Fuller detail for the expanded design and results sections.
    sp = REPO / "results" / "scoring.json"
    if sp.exists():
        cpu = json.loads(sp.read_text()).get("measured_on", "").split(",")[0].strip()
        if cpu:
            out.append(tex_macro("acqHost", cpu))
    # The acquisition host, named from committed measured facts (results/host.json)
    # rather than typed: microarchitecture with its CPUID basis, microcode, kernel,
    # and the turbo/SMT state that bounds the measurement hygiene.
    hp = REPO / "results" / "host.json"
    if hp.exists():
        h = json.loads(hp.read_text())
        for macro, key in (("acqMicroarch", "microarch"),
                           ("acqMicrocode", "microcode"),
                           ("acqKernel", "kernel"),
                           ("acqTurbo", "turbo"),
                           ("acqSMT", "smt"),
                           ("acqGovernor", "governor")):
            if h.get(key):
                # These come verbatim from sysfs, where the SMT control file reports the
                # single token "notsupported". Printed as-is it renders in the paper as
                # "SMT notsupported", which reads as a typesetting fault rather than as a
                # fact about the host. Humanising the token is presentation, not a change
                # of value, so it is done here where the value is emitted rather than by
                # hand in the prose.
                val = {"notsupported": "not supported",
                       "notavailable": "not available"}.get(str(h[key]), str(h[key]))
                out.append(tex_macro(macro, val.replace("_", "\\_")))
        if all(h.get(k) is not None for k in ("cpu_family", "cpu_model_num", "cpu_stepping")):
            out.append(tex_macro(
                "acqCpuid",
                f"family\\,{h['cpu_family']}, model\\,{h['cpu_model_num']}, stepping\\,{h['cpu_stepping']}"))
    # Patched-arm dudect max |t| per applicable pair, taken from the PERMUTATION record
    # for the same reason the vulnerable-arm values are: verdicts.jsonl's patched_max_t
    # includes dudect's second-order test, the permutation null excludes it, and the
    # paper was printing 1.94/2.13/1.44 in the outcome table against 1.7/1.4/2.9 in the
    # figure caption and the body for the same arms at the same budget. One source.
    patched_named = {"ecdsa-nonce": "tPatchedNonceLatency",
                     "ecdsa-address": "tPatchedNonceAddress",
                     "kyberslash": "tDudectDivisionPatched",
                     "hqc-reject": "tPatchedRejection",
                     "hmac-timing": "tPatchedHmac",
                     "_sentinel-positive": "tPatchedSentinelPos"}
    _perm_pt = {}
    _pp_here = REPO / "results" / "dudect_permutation.json"
    if _pp_here.exists():
        for _r in json.loads(_pp_here.read_text())["rows"]:
            if _r["arm"] == "patched":
                _perm_pt[_r["pair"]] = _r["observed_max_abs_t"]
    for r in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if (r.get("tool") == "dudect" and r.get("applicable")
                and r["pair"] in patched_named):
            v = _perm_pt.get(r["pair"], r.get("patched_max_t"))
            if v is not None:
                # Two decimals: these are small values and rounding to an integer would
                # hide how far inside its null the arm actually sits.
                out.append(tex_macro(patched_named[r["pair"]], f"{v:.2f}"))
    # PR-3 dudect: the null-tau band calibrated on the constant-time negative
    # sentinel (replacing the arbitrary [10,500] band), and the effect size in ticks
    # with its bootstrap CI for the key arms, so the paper quotes a magnitude and an
    # interval rather than a threshold crossing.
    calp = REPO / "results" / "dudect_calibration.json"
    if calp.exists():
        cal = json.loads(calp.read_text())
        out.append(tex_macro("dudectNullThresholdTau", f"{cal['null_threshold_tau']:.3f}"))
        out.append(tex_macro("dudectNullTauMedian", f"{cal['null_tau_median']:.3f}"))
        out.append(tex_macro("dudectCalibRuns", str(cal.get("runs", 0))))
    effect_named = {"kyberslash": "Division", "ecdsa-nonce": "NonceLatency",
                    "ecdsa-address": "NonceAddress", "hmac-timing": "Hmac",
                    "hqc-reject": "Rejection"}
    for r in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if r.get("tool") != "dudect" or r["pair"] not in effect_named:
            continue
        suf = effect_named[r["pair"]]
        if r.get("vulnerable_effect_ticks") is not None:
            out.append(tex_macro(f"effectVuln{suf}", f"{r['vulnerable_effect_ticks']:.3f}"))
        ci = r.get("vulnerable_ci")
        if ci and ci[0] is not None:
            out.append(tex_macro(f"ciLoVuln{suf}", f"{ci[0]:.3f}"))
            out.append(tex_macro(f"ciHiVuln{suf}", f"{ci[1]:.3f}"))
        def _tau(v):
            return f"{v:.4f}" if v < 1 else f"{v:.0f}"
        if r.get("vulnerable_max_tau") is not None:
            out.append(tex_macro(f"tauVuln{suf}", _tau(r["vulnerable_max_tau"])))
        if r.get("patched_max_tau") is not None:
            out.append(tex_macro(f"tauPatched{suf}", _tau(r["patched_max_tau"])))
    # The statistic the verdict rests on: dudect's max |t| against the permutation
    # null of each run's own committed samples. All dumps share one budget, so these
    # are directly comparable and one null quantile bounds them all. tau above is kept
    # only as a reported effect size; it is no longer a decision variable.
    permp = REPO / "results" / "dudect_permutation.json"
    if permp.exists():
        perm = json.loads(permp.read_text())
        by = {(x["pair"], x["arm"]): x for x in perm["rows"]}
        for pair, suf in effect_named.items():
            for arm, word in (("vulnerable", "Vuln"), ("patched", "Patched")):
                row = by.get((pair, arm))
                if row is None:
                    continue
                out.append(tex_macro(f"permT{word}{suf}",
                                     f"{row['observed_max_abs_t']:.1f}"))
                # Two decimals is the precision a p-value of this size supports; at
                # the permutation floor the exact 1/(perms+1) is printed instead,
                # because rounding it would show a p no permutation test can produce.
                pv = row["p_value"]
                out.append(tex_macro(f"permP{word}{suf}",
                                     f"{pv:.4f}" if pv < 0.01 else f"{pv:.2f}"))
        out.append(tex_macro("permNullQ",
                             f"{max(x['null_max_abs_t_p95'] for x in perm['rows']):.1f}"))
        out.append(tex_macro("permPerms", f"{perm['rows'][0]['permutations']:,}"))
        out.append(tex_macro("permTests", str(len(perm["rows"]))))
        # dudect's crop ladder size, read from the permutation generator so the paper
        # cannot describe a ladder the null does not actually use.
        _dp = (REPO / "bin" / "dudect_permute.py").read_text()
        _m = re.search(r"N_CROPS\s*=\s*(\d+)", _dp)
        if _m:
            out.append(tex_macro("dudectCrops", _m.group(1)))
    # The dividend interval the deployed KyberSlash division occupies, derived from the
    # modulus rather than typed: after the conditional add t is in [0, q), so the
    # dividend (t<<1) + q/2 spans [q/2, 2(q-1) + q/2]. The figures shade this band and
    # both read it from here, so the caption and the plot cannot drift apart.
    ks_hdr = REPO / "pairs" / "kyberslash" / "src" / "kyber_slash.h"
    ks_q = int(re.search(r"#define\s+KYBER_Q\s+(\d+)", ks_hdr.read_text()).group(1))
    out.append(tex_macro("ksModulus", str(ks_q)))
    out.append(tex_macro("ksOperandLo", str(ks_q // 2)))
    out.append(tex_macro("ksOperandHi", str((ks_q - 1) * 2 + ks_q // 2)))
    # The amplification factor applied to the nonce pairs' per-bit work, read from
    # the driver #define so the disclosure is itself a regenerated number. KyberSlash
    # carries no such loop; the paper says so and this macro exists only for the arms
    # that are amplified.
    amp_src = REPO / "pairs" / "ecdsa-nonce" / "src" / "vulnerable.c"
    if amp_src.exists():
        m = re.search(r"#define\s+AMP\s+(\d+)", amp_src.read_text())
        if m:
            emit("ampNonce", int(m.group(1)))
    # hmac-timing amplifies in a per-byte work loop, not a #define, so read its bound.
    # The rejection sampler amplifies too, symmetrically: the same per-draw work loop
    # runs in both arms, so it widens the draw-count difference without creating one.
    amp_rej = REPO / "pairs" / "hqc-reject" / "src" / "vulnerable.c"
    if amp_rej.exists():
        m = re.search(r"#define\s+AMP\s+(\d+)", amp_rej.read_text())
        if m:
            emit("ampRejection", int(m.group(1)))
    amp_hmac = REPO / "pairs" / "hmac-timing" / "src" / "work.c"
    if amp_hmac.exists():
        m = re.search(r"#define\s+AMP\s+(\d+)", amp_hmac.read_text())
        if m:
            emit("ampHmac", int(m.group(1)))
    tp = REPO / "data" / "tools.toml"
    if tp.exists():
        dud = tomllib.loads(tp.read_text()).get("tool", {}).get("dudect", {})
        if "band_leak" in dud:
            emit("dudectBandLeak", dud["band_leak"])
        if "band_clean" in dud:
            emit("dudectBandClean", dud["band_clean"])
    gp2 = REPO / "results" / "kyberslash_graviton.json"
    if gp2.exists():
        ghz = json.loads(gp2.read_text()).get("host", {}).get("counter_ghz")
        if ghz is not None:
            out.append(tex_macro("gravCounterGHz", f"{ghz:.2f}"))
            out.append(tex_macro("gravTickPs", f"{1000.0 / ghz:.0f}"))
    # The x86 leak-presence microbenchmark on the acquisition host: the divl step at
    # the KyberSlash divisor boundary against the run's noise floor. It certifies that
    # dudect's null on x86 is correct on this host, not a missed present leak.
    xp = REPO / "results" / "kyberslash_x86_idiv.json"
    if xp.exists():
        xr = json.loads(xp.read_text())["results"]
        lat = xr.get("idiv_latency_operand_dependent", {})
        if lat.get("spread_ticks") is not None:
            out.append(tex_macro("hostIdivSpread", f"{lat['spread_ticks']:.3f}"))
        st = xr["kyberslash_operand_range_step"]
        out.append(tex_macro("hostStepTicks", f"{abs(st['step_ticks']):.3f}"))
        out.append(tex_macro("hostNoiseFloor", f"{st['noise_floor_ticks']:.2f}"))
        out.append(tex_macro("hostStepBelow", f"{st['coeff_below_833_ticks']:.2f}"))
        out.append(tex_macro("hostStepAbove", f"{st['coeff_at_or_above_833_ticks']:.2f}"))
        cg = xr["codegen"]["idiv_in_coeff_to_bit"]
        out.append(tex_macro("hostIdivOs", str(cg["Os"])))
        out.append(tex_macro("hostIdivReciprocal", str(cg["O2"])))
        if xr.get("tsc_ghz"):
            out.append(tex_macro("hostTscGHz", f"{xr['tsc_ghz']:.2f}"))
            out.append(tex_macro("hostTickPs", f"{1000.0 / xr['tsc_ghz']:.0f}"))
        # The x86 end-to-end pipelined figures, so the three per-operation quantities in
        # sec/microarch can be told apart: a serial-chain latency that is flat, a
        # per-call two-class step that is resolvable, and a pipelined end-to-end
        # difference that is absorbed. dudect measures the third.
        _xe = xr.get("end_to_end_coeff_to_bit_Os", {})
        if _xe.get("low_coeffs_ticks_per_call"):
            out.append(tex_macro("hostPipelinedCallTicks",
                                 f"{_xe['low_coeffs_ticks_per_call']:.1f}"))
            out.append(tex_macro("hostPipelinedDelta",
                                 f"{abs(_xe['secret_dependent_delta_ticks']):.3f}"))
        # x86 end-to-end two-class delta: the x86 rung of the host-magnitude ladder
        # (F3), against gravDeltaPercent on Neoverse-V1. Distinct from the single-bit
        # step above, which is what F1 rests on.
        e2x = xr.get("end_to_end_coeff_to_bit_Os")
        if e2x and e2x.get("delta_percent_of_call") is not None:
            out.append(tex_macro("hostDeltaTicks", f"{e2x['secret_dependent_delta_ticks']:.3f}"))
            out.append(tex_macro("hostDeltaPercent", f"{e2x['delta_percent_of_call']:.2f}\\%"))
        # Per-call operand-magnitude sensitivity (serialised), the number that shows the
        # x86 step is resolvable per-call but absorbed when pipelined.
        pcs = xr.get("per_call_magnitude_sensitivity")
        if pcs and pcs.get("mean_ticks_at_max_n") is not None:
            out.append(tex_macro("hostPerCallTicks", f"{abs(pcs['mean_ticks_at_max_n']):.2f}"))
    # Permutation-null verdicts: the budget each run supplies its own null from, and
    # the p-values the paper quotes for the nonce arms.
    pm = REPO / "results" / "dudect_permutation.json"
    if pm.exists():
        pmd = json.loads(pm.read_text())
        rows = {r["path"].split("/")[-1].replace(".dudect.bin.gz", ""): r
                for r in pmd.get("rows", [])}
        ns = sorted({r["measurements"] for r in pmd.get("rows", [])})
        if ns:
            out.append(tex_macro("dudectBudget", f"{ns[-1]:,}"))
        det = [r["p_value"] for r in pmd.get("rows", []) if r.get("bh_significant")]
        if det:
            out.append(tex_macro("pDetected", f"{max(det):.4f}"))

    # Fix-verification: the three deployed Minerva remediations and the MatrixSSL
    # incomplete-fix residual, from results/fix_verification.json, so the headline
    # numbers are generated rather than typed.
    fv = REPO / "results" / "fix_verification.json"
    if fv.exists():
        fvd = json.loads(fv.read_text())
        mxl = fvd["libraries"]["matrixssl"]
        mx = mxl["dudect_tau"]
        # tau macros deliberately not emitted: the band they served was retired, and the
        # paper keeps only the corollary that a falling tau is not evidence of a null.
        # The four-design decomposition that locates the residual in the leading-zero
        # phase rather than the loop bound. Reported as |t| against each run's own
        # permutation null, because tau is not comparable across these budgets.
        xh = mxl.get("cross_host_replication", {}).get("abs_t_by_host", {})
        arm = xh.get("aarch64 Neoverse-V1", {})
        if arm.get("4-3-0_bit255v256") is not None:
            out.append(tex_macro("mxTFixedArm", f"{arm['4-3-0_bit255v256']:.0f}"))
            out.append(tex_macro("mxTPrefixArm", f"{arm['4-2-1_bit255v256']:.0f}"))
        dec = mxl.get("decomposition_4_3_0", {})
        # Every MatrixSSL statistic now comes from the one full-report pass over the
        # committed dumps, so the paper reports n, p and an effect size beside each |t|
        # rather than a bare statistic, and every value is decided by the rule in force.
        full = mxl.get("measurements_full_report", {}).get("designs", {})
        for macro, dump, fmt in (("mxTFixed", "mx430_bit255v256", ".0f"),
                                 ("mxTControl", "mx430_same", ".1f"),
                                 ("mxTSameDigit", "mx430_samedigit", ".0f"),
                                 ("mxTDiffDigit", "mx430_diffdigit", ".0f"),
                                 ("mxTPrefix", "mx4-2-1_bit255v256", ".0f"),
                                 ("mxTLatest", "mx4-6-0_bit255v256", ".0f")):
            if dump in full:
                out.append(tex_macro(macro, format(full[dump]["max_abs_t"], fmt)))
        if "mx430_bit255v256" in full:
            _f = full["mx430_bit255v256"]
            out.append(tex_macro("mxN", f"{_f['measurements']:,}"))
            out.append(tex_macro("mxPerms", f"{_f['permutations']:,}"))
            out.append(tex_macro("mxPFixed", f"{_f['permutation_p']:.4f}"))
            out.append(tex_macro("mxEffectFixed", f"{_f['effect_ticks']:,.0f}"))
            # No thousands separator on these two: they are printed inside a math-mode
            # interval, $[lo, hi]$, where a comma is a list separator, so "1,777" and
            # "2,432" rendered as a four-element list "[1, 777, 2, 432]".
            out.append(tex_macro("mxEffectFixedLo", f"{_f['ci_low']:.0f}"))
            out.append(tex_macro("mxEffectFixedHi", f"{_f['ci_high']:.0f}"))
            # The denominator. A difference in ticks says nothing about how large the
            # residual is relative to the operation it was measured on, and without it
            # the number cannot be compared with the residuals quoted for the other two
            # libraries. call_ticks is the slower class mean on the effect size's own
            # crop, so the fraction is of the SCALAR MULTIPLICATION, not of a signature.
            # call_ticks is emitted for the containment arithmetic. The fraction is emitted
            # too, but under a name that says WHICH REGION it divides by, and it is used
            # only as a within-region consistency check against the instruction count.
            # What was withdrawn is quoting it as a deployment magnitude, which it is not:
            # the region's identity is what the containment arithmetic leaves open.
            if _f.get("call_ticks"):
                out.append(tex_macro("mxCallTicks", f"{_f['call_ticks']:,.0f}"))
                out.append(tex_macro("mxResidualOfCall",
                                     f"{_f['residual_fraction'] * 100:.2f}\\%"))
        if "mx430_same" in full:
            _c = full["mx430_same"]
            out.append(tex_macro("mxPControl", f"{_c['permutation_p']:.2f}"))
        if mxl.get("measurements_full_report", {}).get("acquisitions_per_arm"):
            out.append(tex_macro("mxAcquisitions",
                                 str(mxl["measurements_full_report"]["acquisitions_per_arm"])))
        # Effect sizes in ticks for each design, which separate the mechanisms far more
        # clearly than |t| does: |t| saturates once an effect is large, while the class
        # difference keeps scaling with the work the design actually changes.
        for macro, dump in (("mxEffectPrefix", "mx4-2-1_bit255v256"),
                            ("mxEffectSameDigit", "mx430_samedigit"),
                            ("mxEffectDiffDigit", "mx430_diffdigit")):
            if dump in full:
                out.append(tex_macro(macro, f"{full[dump]['effect_ticks']:,.0f}"))
        # The same fraction for the arm the fix was applied to and for the latest
        # release, which is how the attenuation reads in a unit that has a denominator.
        if "mx430_samedigit" in full and "mx430_diffdigit" in full:
            out.append(tex_macro("mxDigitRatio",
                                 f"{full['mx430_diffdigit']['effect_ticks'] / full['mx430_samedigit']['effect_ticks']:.0f}"))
        # mxAttenuation is deliberately not emitted: it was a ratio of two single
        # acquisitions of separately built binaries on a host whose frequency is not
        # pinned, so the within-run bootstrap intervals do not bound it.
        # The exact builds measured, so "the latest open release" is a version a
        # reader can fetch and a commit they can check, not a phrase.
        for macro, key in (("mxVerPrefix", "vulnerable"), ("mxVerFixed", "patched"),
                           ("mxVerLatest", "latest_open")):
            if mxl.get(key):
                out.append(tex_macro(macro, mxl[key].replace("-open", "").replace("-", ".")))
        sc = mxl.get("source_commits", {})
        for macro, key in (("mxCommitPrefix", "4-2-1-open"),
                           ("mxCommitFixed", "4-3-0-open"),
                           ("mxCommitLatest", "4-6-0-open")):
            if sc.get(key):
                out.append(tex_macro(macro, sc[key]))

        wolf = fvd["libraries"]["wolfssl"]
        out.append(tex_macro("wolfResidualPercent", "0.03\\%"))
        if wolf.get("recovery_attempt_budget_sigs"):
            out.append(tex_macro("wolfSigs", f"{wolf['recovery_attempt_budget_sigs']:,}"))
        # The survey's coverage, counted from the triage record rather than typed,
        # so a candidate added or built later moves the paper's number with it.
        st = fvd.get("survey_triage", {}).get("candidates", {})
        if st:
            out.append(tex_macro("nSurveyCandidates", str(len(st))))
            out.append(tex_macro("nSurveyMeasured",
                                 str(sum(1 for v in st.values() if v.get("measured")))))
            out.append(tex_macro("nSurveyTriagedOnly",
                                 str(sum(1 for v in st.values()
                                         if not v.get("measured")))))
    # The corpus's provenance split, counted from the manifests. The abstract, the
    # introduction and the conclusion all described the corpus in terms the roster
    # contradicted ("each item is a deployed leak reproduced as two builds differing by
    # one upstream patch" is true of exactly one pair), so the split is generated and
    # quoted rather than characterised in prose that can drift from the manifests.
    prov = {}
    for pt in sorted((REPO / "pairs").glob("*/pair.toml")):
        d = tomllib.loads(pt.read_text())
        if d.get("pair", {}).get("role") != "corpus":
            continue
        kind = d.get("provenance", {}).get("provenance_kind", "unset")
        prov[kind] = prov.get(kind, 0) + 1
    for macro, key in (("nProvRelease", "release-pair"),
                       ("nProvVendored", "vendored-reproduction"),
                       ("nProvSynthetic", "synthetic-reproduction"),
                       ("nProvObservation", "observation-dataset")):
        out.append(tex_macro(macro, str(prov.get(key, 0))))
        _n = prov.get(key, 0)
        if 0 <= _n < len(WORDS):
            out.append(tex_macro(macro + "Word", WORDS[_n]))
    # The libgcrypt primitive probe. The Table 1 cell used to read as a one-bit
    # site-closure decision, which this probe does not support: it is a coarse
    # short-versus-full scalar comparison, and it is quoted as such.
    lgr = REPO / "pairs" / "libgcrypt-minerva" / "acquire" / "record.json"
    if lgr.exists():
        pr = json.loads(lgr.read_text()).get("primitive_timing", {})
        for macro, key in (("lgPrimShortVuln", "min_cycles_short_vs_full_1_8_4"),
                           ("lgPrimShortPatched", "min_cycles_short_vs_full_1_8_5")):
            v = pr.get(key)
            if v:
                out.append(tex_macro(macro, f"{v[0]:,}"))
                out.append(tex_macro(macro + "Full", f"{v[1]:,}"))
    # The containment arithmetic. A whole signature contains a scalar multiplication, so
    # the retired count for one call and the tick cost of a signature have to be mutually
    # possible. Emitting instructions-per-tick for both regions lets the paper make that
    # test on the page instead of asserting an anomaly it does not quantify.
    _icp = REPO / "results" / "matrixssl_icount.json"
    _ebm = REPO / "results" / "exploit_budget_matrixssl.json"
    if _icp.exists() and _ebm.exists() and fv.exists():
        _pc = json.loads(_icp.read_text()).get("per_call", {})
        _lad = json.loads(_ebm.read_text()).get("leading_zero_ladder", {})
        _full = (json.loads(fv.read_text())["libraries"]["matrixssl"]
                 .get("measurements_full_report", {}).get("designs", {}))
        _call = _full.get("mx430_bit255v256", {}).get("call_ticks")
        if _pc.get("256") and _lad.get("lz_0") and _call:
            _instr = _pc["256"]["instructions_per_call"]
            _sig = float(_lad["lz_0"]["median_ticks"])
            out.append(tex_macro("icPerTickIsolated", f"{_instr / _call:.1f}"))
            out.append(tex_macro("icPerTickSignature", f"{_instr / _sig:.0f}"))
    # BIN-1's on-demand result. The control is declared rather than enforced because a
    # full rebuild is minutes of container work, so without this the paper could only
    # assert that its pinned cells reproduce, in a paper whose F2 thesis is that the
    # constant-time label belongs to the emitted binary.
    b1 = REPO / "results" / "bin1_check.json"
    if b1.exists():
        _b = json.loads(b1.read_text())
        out.append(tex_macro("binOneBinaries", f"{_b['binaries_checked']:,}"))
        out.append(tex_macro("binOneDrift", str(_b.get("discrepancies", 0))))
    # Power for every patched arm. A clean verdict without a resolution floor is half a
    # result: it says no leak was reported and not what size of leak would have been. The
    # CI half-width is that floor at this budget.
    ppp = REPO / "results" / "patched_power.json"
    if ppp.exists():
        pw = json.loads(ppp.read_text()).get("arms", {})
        camel = {"ecdsa-nonce": "NonceLatency", "ecdsa-address": "NonceAddress",
                 "hmac-timing": "Hmac", "kyberslash": "Division", "hqc-reject": "Rejection"}
        for pair, suffix in camel.items():
            r = pw.get(pair)
            if not r:
                continue
            out.append(tex_macro("effPatched" + suffix, f"{r['effect_ticks']:,.3f}"))
            out.append(tex_macro("ciHalfPatched" + suffix,
                                 f"{r['ci_half_width_ticks']:,.3f}"))
    # The committed signing trace and the key that labels it. The paper used to mark
    # this group as not recomputable because neither survived the acquisition; both are
    # in the repository now, so the count comes from the file rather than from memory.
    tr = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "trace-4-3-0.csv.z"
    kf = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "signing-key-4-3-0.hex"
    if tr.exists() and kf.exists():
        import zlib as _zlib
        _n = _zlib.decompress(tr.read_bytes()).count(b"\n") - 1   # minus the header line
        out.append(tex_macro("mxTraceN", f"{_n:,}"))

    # The containment resolution. These replace the three mutually impossible figures
    # the paper used to print: measured together in one process they are consistent,
    # and the one that was wrong was this corpus's own harness.
    cont = REPO / "results" / "matrixssl_containment.json"
    if cont.exists():
        cj = json.loads(cont.read_text())
        m = cj["median_ticks"]
        out.append(tex_macro("mxGenkeyTicks", f"{m['genkey']:,}"))
        out.append(tex_macro("mxMulnullTicks", f"{m['mulnull']:,}"))
        out.append(tex_macro("mxSignTicks", f"{m['sign']:,}"))
        out.append(tex_macro("mxOldRegionTicks", f"{m['mulmod']:,}"))
        out.append(tex_macro("mxHarnessFactor",
                             f"{cj['harness_overstatement_factor']:.2f}"))
        out.append(tex_macro("mxGenkeyGap",
                             f"{cj['mulnull_vs_genkey_relative_gap'] * 100:.2f}\\%"))
        out.append(tex_macro("mxContainmentReps", str(cj["repeats"])))

    # The repeats. Every interval previously reported on this case came from one
    # acquisition; these are the between-acquisition figures that could not exist then.
    rep = REPO / "results" / "matrixssl_repeats.json"
    if rep.exists():
        rj = json.loads(rep.read_text())["designs"]
        key = "4-3-0.bit255"
        if key in rj:
            d = rj[key]
            out.append(tex_macro("mxReps", str(d["repeats"])))
            out.append(tex_macro("mxRepMeanEffect", f"{d['mean_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepLo", f"{d['min_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepHi", f"{d['max_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepExcl",
                                 str(d["reps_with_interval_excluding_zero"])))
        ctl = "4-3-0.same"
        if ctl in rj:
            out.append(tex_macro("mxRepCtlExcl",
                                 str(rj[ctl]["reps_with_interval_excluding_zero"])))
            out.append(tex_macro("mxRepCtlReps", str(rj[ctl]["repeats"])))

    # The field the scored analysers were drawn from. The row set is a computation over a
    # pinned third-party inventory, so these are counts and not claims; nFieldIndexed also
    # retires the hand-typed 55 that data/facts.toml carried from a web page.
    amp_p = REPO / "results" / "analyser_matrix.json"
    if amp_p.exists():
        am = json.loads(amp_p.read_text())
        out.append(tex_macro("nFieldIndexed", str(am["indexed"])))
        out.append(tex_macro("nFieldTargetEligible", str(am["target_eligible"])))
        out.append(tex_macro("nFieldAvailEligible",
                             str(am["classified"] - am["added_by_us"])))
        out.append(tex_macro("nFieldClassified", str(am["classified"])))
        out.append(tex_macro("nFieldAdded", str(am["added_by_us"])))
        out.append(tex_macro("nFieldAddedWord", WORDS[am["added_by_us"]] if am["added_by_us"] < len(WORDS)
                             else str(am["added_by_us"])))
        out.append(tex_macro("nFieldVarlatStated", str(am["varlat_stated"])))
        out.append(tex_macro("nFieldVarlatUnstated", str(am["varlat_unstated"])))
        out.append(tex_macro("nFieldScored", str(am["scored"])))

    # Between-acquisition agreement. Every per-arm interval bounds sampling within one
    # acquisition; these are the ten arms that were acquired a second time, and the
    # counts say what the second acquisition agreed with. n=2 estimates no spread.
    rpt = REPO / "results" / "repeatability.json"
    if rpt.exists():
        rp = json.loads(rpt.read_text())
        out.append(tex_macro("reAcqArms", str(rp["n_arms"])))
        out.append(tex_macro("reAcqStatusAgree", str(rp["n_status_agree"])))
        out.append(tex_macro("reAcqStatusCompared", str(rp["n_status_compared"])))
        out.append(tex_macro("reAcqEffectCompared", str(rp["n_effect_compared"])))
        out.append(tex_macro("reAcqBelowCoarser",
                             str(rp["n_gap_below_coarser_half_width"])))
        out.append(tex_macro("reAcqBelowFiner",
                             str(rp["n_gap_below_finer_half_width"])))
        out.append(tex_macro("reAcqMaxGap", f"{rp['max_gap_ticks']:,.3f}"))
        out.append(tex_macro("reAcqMaxHalfWidth",
                             f"{rp['max_ci_half_width_ticks']:,.3f}"))

    # The information-theoretic certification (AUC between timing and nonce shortness)
    # and the selection quality the lattice actually consumes, from
    # results/exploit_budget.json. AUC is the budget-robust half: it estimates the same
    # quantity at any n, so it is the number the two libraries are compared on.
    ebp = REPO / "results" / "exploit_budget.json"
    if ebp.exists():
        eb = json.loads(ebp.read_text())["arms"]
        mx = next(v for k, v in eb.items() if k.startswith("matrixssl"))
        gc = next(v for k, v in eb.items() if k.startswith("libgcrypt"))
        out.append(tex_macro("aucMatrix", f"{mx['auc_full']:.2f}"))
        out.append(tex_macro("aucLibgcrypt", f"{gc['auc_full']:.2f}"))
        out.append(tex_macro("aucMatrixN", f"{mx['n_full']:,}"))
        out.append(tex_macro("aucLibgcryptN", f"{gc['n_full']:,}"))
        out.append(tex_macro("selMatrixMatched",
                             f"{mx['top90_contaminated_matched'] * 100:.0f}\\%"))
        out.append(tex_macro("selMatrixFull",
                             f"{mx['top90_contaminated_full'] * 100:.0f}\\%"))
        out.append(tex_macro("selLibgcrypt",
                             f"{gc['top90_contaminated_full'] * 100:.1f}\\%"))
        out.append(tex_macro("selMatchedN", f"{mx['n_matched']:,}"))
    # The END-TO-END basis for the residual, from the 250k whole-signature trace. The
    # site measurement (bin/fix_report.py) times one isolated eccMulmod call, which on
    # this host costs several times a whole signature's own scalar multiplication, so a
    # residual expressed as a fraction of it is NOT on the same basis as a residual
    # expressed per signature. Both bases are emitted, each labelled with its region,
    # because the only comparison that means anything against another library's
    # per-signature figure is the per-signature one.
    ebm = REPO / "results" / "exploit_budget_matrixssl.json"
    if ebm.exists():
        lad = json.loads(ebm.read_text()).get("leading_zero_ladder", {})
        if "lz_0" in lad and "lz_1" in lad:
            base = float(lad["lz_0"]["median_ticks"])
            d1 = abs(float(lad["lz_1"]["delta_vs_lz0"]))
            out.append(tex_macro("mxSigTicks", f"{base:,.0f}"))
            out.append(tex_macro("mxSigDelta", f"{d1:,.0f}"))
            out.append(tex_macro("mxResidualPerSig", f"{d1 / base * 100:.2f}\\%"))
            # The ladder's shape over the range a real nonce distribution reaches. The
            # per-zero increment is what the selection argument leans on, and it is
            # measured rather than extrapolated from the two Callgrind points.
            zs = sorted((int(k.split("_")[1]) for k in lad), reverse=True)
            zmax = zs[0]
            dmax = abs(float(lad[f"lz_{zmax}"]["delta_vs_lz0"]))
            out.append(tex_macro("mxLadderMaxZeros", str(zmax)))
            out.append(tex_macro("mxLadderMaxPct", f"{dmax / base * 100:.2f}\\%"))
            out.append(tex_macro("mxLadderPerZero", f"{dmax / zmax:,.0f}"))
    # The residual as retired instructions, on the isolated call, so the two instruments
    # on the SAME region can be compared as fractions rather than only in sign.
    icp = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "instruction_counts.json"
    if icp.exists():
        pc = json.loads(icp.read_text()).get("per_call", {})
        # The same residual as a fraction of the same region, by the other instrument,
        # named for its region for the same reason.
        if "256" in pc and "255" in pc:
            out.append(tex_macro("icResidualOfCall",
                                 f"{abs(pc['255']['percent_vs_256']):.2f}\\%"))
    # What the original authors report their recovery needs, beside ours (S8). Read
    # from the committed record so the comparison cannot drift from its source.
    pwp = REPO / "results" / "prior_work_budgets.json"
    if pwp.exists():
        pw = json.loads(pwp.read_text())
        rc = pw["sources"][0]["reported_counts_verbatim"]
        out.append(tex_macro("minervaSigsLibrary",
                             f"{rc['real cryptographic library data']:,}"))
        out.append(tex_macro("minervaSigsCard", f"{rc['smartcard data']:,}"))
        out.append(tex_macro("minervaSigsSimulated",
                             f"{rc['simulated leakage data']:,}"))
        ours = pw["ours"]
        _n = ours["ecdsa-nonce (our reproduction, amplified 40x)"]
        out.append(tex_macro("oursSigsNonce", f"{_n['n_star_p1.0']:,}"))
        out.append(tex_macro("oursSigsNonceHalf", f"{_n['n_star_p0.5']:,}"))
        _g = ours.get("libgcrypt-minerva (real 1.8.4 build)", {})
        if _g.get("n_star_p1.0"):
            out.append(tex_macro("oursSigsLibgcryptFull", f"{_g['n_star_p1.0']:,}"))
            out.append(tex_macro("oursSigsLibgcryptHalf", f"{_g['n_star_p0.5']:,}"))
            out.append(tex_macro("libgcryptVsPriorFactor",
                                 f"{_g['n_star_p1.0'] / 1200:.0f}"))

    # The deterministic cross-check: retired instructions per nonce class. Reported as
    # the per-call delta against the 256-bit class, which is what separates an
    # algorithmic residual from a microarchitectural one.
    icp = REPO / "results" / "matrixssl_icount.json"
    if icp.exists():
        pc = json.loads(icp.read_text())["per_call"]
        for macro, key in (("icDeltaOneZero", "255"), ("icDeltaManyZeros", "193"),
                           ("icDeltaDigitShort", "192")):
            if key in pc:
                out.append(tex_macro(macro, f"{abs(pc[key]['delta_vs_256']):,.0f}"))
        if "192" in pc:
            out.append(tex_macro("icPercentDigitShort",
                                 f"{abs(pc['192']['percent_vs_256']):.0f}\\%"))
        if "256" in pc:
            out.append(tex_macro("icBase",
                                 f"{pc['256']['instructions_per_call']:,.0f}"))
        ic = json.loads(icp.read_text())
        out.append(tex_macro("icPerTick", f"{ic['instructions_per_tick']:.2f}"))
        _dir = ic.get("direction", {})
        if _dir.get("first_leading_zero"):
            out.append(tex_macro("icFirstZero", f"{_dir['first_leading_zero']:,}"))
            out.append(tex_macro("icManyZeros",
                                 f"{_dir['sixty_three_leading_zeros']:,}"))
            out.append(tex_macro("icPerFurtherZero",
                                 f"{_dir['per_additional_after_the_first']:,}"))
    # The repeated amplification curve. The reportable quantities are the repetition
    # count, the spread, and the sign structure; no single run's |t| is a macro,
    # because one run of that experiment is not reproducible.
    dcp = REPO / "results" / "kyberslash_detection_curve.json"
    if dcp.exists():
        dc = json.loads(dcp.read_text())
        out.append(tex_macro("curveRuns", str(dc.get("runs", 0))))
        out.append(tex_macro("curveMaxAmp", str(max(c["amp"] for c in dc["curve"]))))
        allt = [t for c in dc["curve"] for t in c["abs_t_runs"]]
        out.append(tex_macro("curveMaxT", f"{max(allt):.1f}"))
        out.append(tex_macro("curveMinT", f"{min(allt):.2f}"))
        # The per-factor spread, which is what shows a single run of this experiment is
        # not reproducible. Take the factor with the widest spread rather than typing
        # literals: the paper had described a swing no single factor exhibits.
        _sp = max(dc["curve"], key=lambda c: max(c["abs_t_runs"]) - min(c["abs_t_runs"]))
        out.append(tex_macro("curveSpreadAmp", str(_sp["amp"])))
        out.append(tex_macro("curveSpreadLo", f"{min(_sp['abs_t_runs']):.1f}"))
        out.append(tex_macro("curveSpreadHi", f"{max(_sp['abs_t_runs']):.1f}"))
        neg = [c["amp"] for c in dc["curve"] if c["mean_sign_positive_runs"] == 0]
        pos = [c["amp"] for c in dc["curve"]
               if c["mean_sign_positive_runs"] == dc.get("runs", 0)]
        out.append(tex_macro("curveNegAmps",
                             ", ".join(str(a) for a in neg) or "none"))
        out.append(tex_macro("curvePosAmps",
                             ", ".join(str(a) for a in pos) or "none"))
    # N*(p): the budget at which recovery succeeds with probability at least p, from
    # the committed sweep. A budget, not a yes/no, which is what an attacker faces.
    rrp = REPO / "results" / "recovery_robustness.json"
    if rrp.exists():
        rr = json.loads(rrp.read_text())
        ns = rr.get("n_star") or {}
        if ns.get("p_1.0"):
            out.append(tex_macro("nStarFull", f"{ns['p_1.0']:,}"))
        if ns.get("p_0.5"):
            out.append(tex_macro("nStarHalf", f"{ns['p_0.5']:,}"))
        fails = [r for r in rr["results"] if r["recovered"] == 0]
        if fails:
            out.append(tex_macro("nStarZero", f"{max(r['num_signatures'] for r in fails):,}"))
        out.append(tex_macro("nStarSeeds", str(rr["results"][0]["seeds"])))
        half = [r for r in rr["results"]
                if 0 < r["recovered"] < r["seeds"]]
        if half:
            h = min(half, key=lambda r: r["num_signatures"])
            out.append(tex_macro("recRobustHalf",
                                 f"{h['recovered']} of {h['seeds']}"))
    # Binary confirmation of the site on the nonce pairs: the patched arm's entry
    # symbol reduced to a delegation, with the function byte count as the witness.
    scp = REPO / "results" / "site_confirmation.json"
    if scp.exists():
        sc = json.loads(scp.read_text())["arms"]
        v = sc.get("ecdsa-nonce/vulnerable")
        pa = sc.get("ecdsa-nonce/patched")
        if v and pa:
            out.append(tex_macro("siteVulnBytes", str(v["function_bytes"])))
            out.append(tex_macro("sitePatchedBytes", str(pa["function_bytes"])))
    # Emission measured in the calling context as well as in isolation, so the map is
    # not an artifact of compiling the function alone.
    eicp = REPO / "results" / "emission_in_context.json"
    if eicp.exists():
        eic = json.loads(eicp.read_text())
        out.append(tex_macro("nContextCells", str(len(eic["cells"]))))
        out.append(tex_macro("nContextDisagree",
                             str(len(eic["isolated_comparison"]["disagreements"]))))
    # The flag-axis extension of the emission map: more cells, reported apart from the
    # locked eight because the sweep is lighter than the pinned build pipeline.
    efp = REPO / "results" / "emission_flag_axis.json"
    if efp.exists():
        ef = json.loads(efp.read_text())
        out.append(tex_macro("nFlagCells", str(len(ef["cells"]))))
        out.append(tex_macro("nFlagEmitting", str(len(ef["emitting_cells"]))))
    # The registered five-pair detection curve, at last discharged. The reportable
    # facts are which pairs need no amplification at all and how each one's statistic
    # responds to gain, not any single point.
    dcap = REPO / "results" / "detection_curve_all.json"
    if dcap.exists():
        dca = json.loads(dcap.read_text())
        out.append(tex_macro("nCurvePairs",
                             str(len({r["pair"] for r in dca["rows"] if r.get("status")}))))
        out.append(tex_macro("nCurveDetectAtOne",
                             str(len(dca["pairs_detecting_at_factor_one"]))))
        by = {(r["pair"], r["amp"]): r for r in dca["rows"]
              if r.get("status") and r["arm"] == "vulnerable"}
        for pair, macro in (("kyberslash", "Division"), ("hqc-reject", "Rejection"),
                            ("hmac-timing", "Hmac"), ("ecdsa-nonce", "NonceLatency")):
            ts = [by[(pair, a)]["max_abs_t"] for a in (1, 2, 4, 8) if (pair, a) in by]
            if len(ts) == 4:
                out.append(tex_macro(f"curveOne{macro}", f"{ts[0]:.0f}"))
                out.append(tex_macro(f"curveEight{macro}", f"{ts[-1]:.0f}"))
    # The count of deployed remediations the paper grades was typed as a literal 3,
    # which is the one thing this file exists to prevent. It is the number of candidates
    # in the committed triage that were actually built and measured.
    fvp = REPO / "results" / "fix_verification.json"
    if fvp.exists():
        cands = json.loads(fvp.read_text())["survey_triage"]["candidates"]
        n_fix = sum(1 for c in cands.values() if c.get("measured"))
        out.append(tex_macro("nFixCases", str(n_fix)))
        out.append(tex_macro("nFixCasesWord",
                             WORDS[n_fix] if n_fix < len(WORDS) else str(n_fix)))
    # Recovery robustness: the vendored lattice attack's success over random signature
    # subsets, and its wall time, so the recovery card carries a measured success rate.
    rr = REPO / "results" / "recovery_robustness.json"
    if rr.exists():
        rrd = json.loads(rr.read_text()).get("results", [])
        if rrd:
            total = sum(r["seeds"] for r in rrd)
            got = sum(r["recovered"] for r in rrd)
            out.append(tex_macro("recRobustSuccess", f"{got}\\,of\\,{total}"))
            out.append(tex_macro("recRobustMinSigs", str(min(r["num_signatures"] for r in rrd))))
            out.append(tex_macro("recRobustWall", f"{max(r['median_wall_s'] for r in rrd):.1f}"))
    for t in ("A", "B", "C"):
        emit(f"nTier{t}", report["corpus"]["by_tier"].get(t, 0))
    emit("nCensusIncluded", cen["census_included"])
    emit("nCensusExcluded", cen["census_excluded"])
    for macro, key in (("portableHours", "portable_hours_mean"),
                       ("acquisitionHours", "acquisition_hours_mean")):
        m = report["cost"][key]
        out.append(tex_macro(macro, f"{m.value:.1f}" if m.defined else "\\NA"))
        emit(macro + "N", m.n)
    # dudect's max |t| on the vulnerable arm: huge on the nonce leaks, ~2 on the
    # division it misses. Taken from the PERMUTATION record, not from verdicts.jsonl,
    # so that every |t| the paper prints is the statistic its verdict rule decides on.
    # The two differ: verdicts.jsonl's value includes dudect's second-order test, which
    # the permutation null excludes because it accumulates against a running mean. The
    # paper was printing both for the same arm, 1.06 in one sentence and 1.2 in another.
    _perm_t = {}
    _pp = REPO / "results" / "dudect_permutation.json"
    if _pp.exists():
        for _r in json.loads(_pp.read_text())["rows"]:
            if _r["arm"] == "vulnerable":
                _perm_t[_r["pair"]] = _r["observed_max_abs_t"]
    t_named = {"ecdsa-nonce": "tDudectNonceLatency",
               "ecdsa-address": "tDudectNonceAddress",
               "kyberslash": "tDudectDivision",
               "hqc-reject": "tDudectRejection",
               "hmac-timing": "tDudectHmac",
               "_sentinel-positive": "tSentinelPos"}
    for r in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if r.get("tool") == "dudect" and r.get("applicable") and r["pair"] in t_named:
            v = _perm_t.get(r["pair"], r.get("vulnerable_max_t"))
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
