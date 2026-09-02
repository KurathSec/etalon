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
import math
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
        # Two partitions of the recall-eligible set that the paper had been
        # describing in prose and getting wrong. Both are read off declarations
        # the corpus already makes, so neither can drift from what runs.
        #
        # By recovery runtime: the split's promise is that verification reruns
        # from a cold clone, and for most of these pairs that is true only given
        # the pinned recovery image, because lattice reduction needs fpylll and
        # the upstream curve module is GPL and so lives in the image rather than
        # in this MIT tree. Only the pairs declaring runtime = "pure" rerun on a
        # stock interpreter alone.
        **_recovery_runtime_split(tiers),
        # By whether any analyser is applicable at all. tab:blindspot prints one
        # row per corpus pair carrying at least one applicable analyser row, which
        # is NOT the recall-eligible set: it takes in tier C and leaves out every
        # pair whose observations come with no program to run.
        **_analyser_reach_split(corpus, tiers),
    }


def _recovery_runtime_split(tiers: dict) -> dict:
    names = tiers.get("A", []) + tiers.get("B", [])
    pure = []
    for n in names:
        d = tomllib.loads((REPO / "pairs" / n / "pair.toml").read_text())
        if d.get("recovery", {}).get("runtime") == "pure":
            pure.append(n)
    return {"recall_eligible_pure_recovery": len(pure),
            "recall_eligible_pure_recovery_names": sorted(pure),
            "recall_eligible_image_recovery": len(names) - len(pure)}


def _analyser_reach_split(corpus: list, tiers: dict) -> dict:
    reach = {}
    for row in read_jsonl(REPO / "results" / "verdicts.jsonl"):
        if row.get("applicable"):
            reach[row["pair"]] = reach.get(row["pair"], 0) + 1
    scored = sorted(n for n, _ in corpus if reach.get(n))
    eligible = set(tiers.get("A", []) + tiers.get("B", []))
    return {"analyser_scored_pairs": len(scored),
            "analyser_scored_names": scored,
            # The two ways the scored set and the recall-eligible set differ.
            "analyser_scored_not_eligible": len([n for n in scored if n not in eligible]),
            "analyser_scored_eligible": len([n for n in scored if n in eligible]),
            "eligible_no_analyser": len([n for n in sorted(eligible) if not reach.get(n)])}


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
        elif ("no runnable program" in reason or "no harness built here" in reason):
            # The observation-only pairs (no runnable program), the pairs that ship
            # source but for which no harness was built for this tool (an effort
            # boundary), and the four varlat/binsec ECDSA rows whose pinned images
            # cannot build the OpenSSL-linked arm (a measured incapacity, not an
            # effort boundary) are counted here: none is a mechanism exclusion, and
            # the first two were once split off wrongly, leaving the counts not
            # summing to the inapplicable total. All three spellings bin/score.py
            # emits carry one of the two accepted substrings. A retired spelling was
            # tolerated here once, which hid six stale rows; `bin/score.py --rescore`
            # refreshes reasons, so a stale row now shows up as an unclassified reason.
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


class _Provenance:
    """Which committed record each emitted macro was read from.

    Switched on by --provenance. Every read of a file under the repository is noted
    while the report and the macros are produced; a macro is attributed to the files
    read since the previous macro, or, when none were, to the same files as that
    macro. The section functions run before any macro is emitted, so their reads are
    kept by section and replayed at the point in as_tex where the section's counts
    are emitted. The attribution is therefore observed, not hand-maintained, and a
    new emitter cannot be left out of the table by forgetting to register it.
    """

    def __init__(self):
        self.active = False
        self.section = None
        self.by_section: dict[str, list[str]] = {}
        self.pending: list[str] = []
        self.last: list[str] = []
        self.rows: list[tuple[str, str, str]] = []

    def _rel(self, path) -> str | None:
        try:
            q = Path(path).resolve()
        except (OSError, TypeError):
            return None
        try:
            rel = str(q.relative_to(REPO))
        except ValueError:
            return None
        if rel.startswith("paper/"):
            return None
        return rel

    def note_read(self, path) -> None:
        rel = self._rel(path)
        if rel is None:
            return
        # A glob over pairs/*/pair.toml reads every manifest; the record is the set.
        if rel.startswith("pairs/") and rel.endswith("/pair.toml"):
            rel = "pairs/*/pair.toml"
        bucket = self.by_section.setdefault(self.section, []) if self.section else self.pending
        if rel not in bucket:
            bucket.append(rel)

    def use(self, section: str) -> None:
        """Replay a section function's reads as the context for the next macros."""
        self.pending = list(self.by_section.get(section, []))

    def note_macro(self, name: str, line: int) -> None:
        files = self.pending if self.pending else self.last
        self.last = list(files)
        self.pending = []
        self.rows.append((name, f"bin/regen.py:{line}", ", ".join(files) or "(none read)"))

    def install(self) -> None:
        import builtins
        import io
        self.active = True
        prov = self
        _read_text, _read_bytes, _open = Path.read_text, Path.read_bytes, builtins.open

        def read_text(self_, *a, **k):
            prov.note_read(self_)
            return _read_text(self_, *a, **k)

        def read_bytes(self_, *a, **k):
            prov.note_read(self_)
            return _read_bytes(self_, *a, **k)

        def open_(file, mode="r", *a, **k):
            if "r" in str(mode) and isinstance(file, (str, Path)):
                prov.note_read(file)
            return _open(file, mode, *a, **k)

        Path.read_text, Path.read_bytes, builtins.open = read_text, read_bytes, open_
        io.open = open_

    def table(self) -> str:
        """The provenance table, as chunked tabulars so no float overflows a page."""
        def esc(t: str) -> str:
            return t.replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%")
        # Collapse the spelled-out variants onto their digit macro: nPairs, nPairsWord
        # and nPairsWordCap are one number.
        names = {n for n, _, _ in self.rows}
        rows = []
        for name, gen, rec in self.rows:
            base = name
            for suf in ("WordCap", "Word"):
                if name.endswith(suf) and name[: -len(suf)] in names:
                    base = None
                    break
            if base is None:
                continue
            variants = "".join(
                f", +{suf}" for suf in ("Word", "WordCap") if name + suf in names)
            rows.append((name + variants, gen, rec))
        rows.sort(key=lambda r: (r[2], r[0]))
        out = ["% GENERATED by bin/regen.py --provenance. Do not hand-edit.",
               "% One row per macro numbers.tex defines: the macro, the emitter line that",
               "% produced it, and the committed record(s) it was read from, observed by",
               "% instrumenting every file read during generation.",
               f"% {len(rows)} macros after collapsing the spelled-out variants."]
        chunk = 44
        for i in range(0, len(rows), chunk):
            out.append("\\begin{center}\\scriptsize")
            out.append("\\begin{tabular}{@{}"
                       ">{\\raggedright\\arraybackslash}p{0.30\\linewidth}"
                       ">{\\raggedright\\arraybackslash}p{0.15\\linewidth}"
                       ">{\\raggedright\\arraybackslash}p{0.47\\linewidth}@{}}")
            out.append("\\toprule\nMacro & Generator & Record \\\\\n\\midrule")
            def brk(s):
                # A path or an emitter line is one unbreakable token to TeX; allow a
                # break after every separator so a cell wraps instead of overflowing.
                # esc() has already turned _ into \_, so break after that token too.
                out_s = esc(s)
                for sep in ("/", ".", ":", ",", "\\_"):
                    out_s = out_s.replace(sep, sep + "\\allowbreak{}")
                return out_s
            def brk_name(s):
                # A macro name has no separators; allow a break before each capital.
                return re.sub(r"(?<=[a-z0-9])([A-Z])", lambda m: "\\allowbreak{}" + m.group(1), esc(s))
            for name, gen, rec in rows[i:i + chunk]:
                out.append(f"\\texttt{{\\textbackslash{{}}{brk_name(name)}}} & "
                           f"\\texttt{{{brk(gen)}}} & \\texttt{{{brk(rec)}}} \\\\")
            out.append("\\bottomrule\n\\end{tabular}\n\\end{center}")
        return "\n".join(out) + "\n"


_prov = _Provenance()


def tex_macro(name: str, body: str) -> str:
    # A LaTeX control sequence is letters only. \foo255 parses as \foo followed by
    # 255, so \newcommand on such a name fails with "Missing \begin{document}" at the
    # macro, which points at the wrong thing entirely and has cost this project two
    # silent build failures. Refuse it here, where the message can name the cause.
    if not name.isalpha():
        raise ValueError(
            f"macro name {name!r} is not letters-only; LaTeX cannot define it. "
            f"Spell any digits out (icDelta255 -> icDeltaOneZero).")
    if _prov.active:
        import inspect
        line = 0
        for fr in inspect.stack()[1:]:
            if fr.filename == __file__ and fr.function not in ("emit", "tex_macro"):
                line = fr.lineno
                break
        _prov.note_macro(name, line)
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
        # How many instruments INST-1 turns the sentinel discipline on. Counted from
        # the control's own source, the same way the control count is, so the paper
        # cannot say "every instrument" over a list of three or go stale when a
        # fourth is added. The names come from the check labels the control prints.
        _inst = re.search(r"def [a-z_]*inst[_0-9]*\(.*?(?=\ndef )", _src,
                          re.S | re.I)
        if _inst:
            _labels = re.findall(r'checks\.append\("([^"]+)"\)', _inst.group(0))
            emit("nInstrumentsExercised", len(_labels))

    c = report["corpus"]
    _prov.use("corpus")
    emit("nPairs", c["pairs_total"])
    emit("nPairsCorpus", c["pairs_corpus"])
    emit("nPairsSentinel", c["pairs_sentinel"])
    emit("nRecallEligible", c["recall_eligible_pairs"])
    emit("nRecallPureRecovery", c["recall_eligible_pure_recovery"])
    emit("nRecallImageRecovery", c["recall_eligible_image_recovery"])
    emit("nBlindspotPairs", c["analyser_scored_pairs"])
    emit("nBlindspotTierC", c["analyser_scored_not_eligible"])
    emit("nBlindspotEligible", c["analyser_scored_eligible"])
    emit("nEligibleNoAnalyser", c["eligible_no_analyser"])

    cen = report["census"]
    _prov.use("census")
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
    _prov.use("verdicts")
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
    _prov.use("cost")
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
        out.append(tex_macro("gravHostShort", "Graviton3"))
        out.append(tex_macro("gravHost", "AWS Graviton3 (Neoverse\\,V1)"))
        # The one aarch64 build cell, named from its committed textprint path. It is
        # outside the digest-pinning discipline (an unpinned host compiler, a textprint
        # of the vulnerable arm only, no .text digest), and the paper says so where it
        # is used; the name is generated so the compiler version is never typed.
        _tp = g["results"]["codegen"].get("textprint", "")
        if _tp:
            out.append(tex_macro("gravCell", Path(_tp).parent.name.replace("_", "\\_")))
        out.append(tex_macro("gravOsUdiv", str(codegen["Os"])))
        # The operand-MAGNITUDE spread across the KyberSlash range (low- vs
        # high-coefficient udiv latency), which is the leak; the single-coefficient
        # boundary step (gravBoundaryStep) is sub-noise, measured directly on aarch64.
        out.append(tex_macro("gravStepTicks",
                             f"{mag['high_coeff_ticks_per_udiv'] - mag['low_coeff_ticks_per_udiv']:.2f}"))
        out.append(tex_macro("gravBoundaryStep", f"{abs(bnd['step_ticks']):.5f}"))
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
        # The whole-sweep spread of the serial-chain udiv latency, the same quantity
        # hostIdivSpread is on x86, so the six-number table compares like with like.
        _gl = g["results"]["udiv_latency_operand_dependent"]["ticks_per_udiv"]
        out.append(tex_macro("gravSweepSpread", f"{max(_gl.values()) - min(_gl.values()):.3f}"))
        # The end-to-end percentage was produced by a program that generated the two
        # classes with different constant reductions inside the timed loop; correcting
        # the identical x86 twin took its delta from 1.6% to ~0, so this number is
        # confounded and pending re-measurement. Emit NA until re-run, so no confounded
        # figure can reach the paper. The serial-chain udiv latency curve above is
        # unaffected (fixed dividend, identical code both classes) and carries I2, the host index.
        if e2e.get("MEASUREMENT_STATUS", "").startswith("CONFOUNDED"):
            out.append(tex_macro("gravDeltaTicks", None))
            out.append(tex_macro("gravDeltaPercent", None))
        else:
            out.append(tex_macro("gravDeltaTicks", f"{e2e['secret_dependent_delta_ticks']:.3f}"))
            out.append(tex_macro("gravDeltaPercent", f"{e2e['delta_percent_of_call']:.1f}\\%"))
        # The aarch64 control is reported as a permutation p and a counter-resolution
        # fact, not as a tau: on this counter a coeff_to_bit call is a handful of ticks,
        # so a per-call tau is not a meaningful effect size (see the JSON note).
        # The spread behind the end-to-end delta is the min and max over the repeats
        # the harness runs (measure_arm.py), not a confidence interval, and it is printed
        # as a range beside the point estimate; no null exists for this estimator.
        if e2e.get("delta_ci_ticks"):
            out.append(tex_macro("gravDeltaRangeLo", f"{e2e['delta_ci_ticks'][0]:.3f}"))
            out.append(tex_macro("gravDeltaRangeHi", f"{e2e['delta_ci_ticks'][1]:.3f}"))
        _ma = REPO / "pairs" / "kyberslash" / "graviton" / "measure_arm.py"
        _mr2 = re.search(r"for _ in range\((\d+)\)", _ma.read_text()) if _ma.exists() else None
        if _mr2:
            emit("gravDeltaRepeats", int(_mr2.group(1)))
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
        # Which core the acquisitions pin to, and what kind: a hybrid part has dividers
        # of two designs, so the core type is part of the host index, not a detail.
        if h.get("pinned_core_type"):
            out.append(tex_macro("acqCoreType", str(h["pinned_core_type"])))
        if h.get("pinned_cpu") is not None:
            out.append(tex_macro("acqPinnedCpu", str(h["pinned_cpu"])))
        if h.get("hybrid") is not None:
            out.append(tex_macro("acqPartKind", "hybrid" if h["hybrid"] else "uniform"))
        _fk = h.get("frequency_khz") or {}
        if _fk.get("scaling_min") and _fk.get("scaling_max"):
            out.append(tex_macro("acqFreqMinGHz", f"{_fk['scaling_min'] / 1e6:.1f}"))
            out.append(tex_macro("acqFreqMaxGHz", f"{_fk['scaling_max'] / 1e6:.1f}"))
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
    # PR-3 dudect, kept as the record of a retired rule: the null-tau band was
    # calibrated on the constant-time negative sentinel (replacing the arbitrary
    # [10,500] band) and then retired by PR-4's permutation verdict, so these
    # macros document what the retired band was and no verdict reads them. The
    # effect size in ticks with its bootstrap CI for the key arms still stands, so
    # the paper quotes a magnitude and an interval rather than a threshold crossing.
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
        # The lowest uncorrected p among the arms the false-discovery control declines,
        # and how many of those sit below 0.05. PR-4 predicted at least one; after the
        # patched division arm was re-acquired under upstream's fix there are none, so
        # the paper states the observed floor rather than a row it remembers.
        _ns = [x["p_value"] for x in perm["rows"] if not x.get("bh_significant")]
        if _ns:
            out.append(tex_macro("permPLowestDeclined", f"{min(_ns):.2f}"))
            out.append(tex_macro("permNBelowFive", str(sum(1 for x in _ns if x < 0.05))))
            out.append(tex_macro("permNBelowFiveWord",
                                 {0: "no", 1: "one", 2: "two", 3: "three"}.get(
                                     sum(1 for x in _ns if x < 0.05), "several")))
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
        # The ablation and the aggregated granularity, both added for the fifteenth
        # review. The ablation is what says whether the per-call effect belongs to the
        # divider: the identical two-class design with the division replaced by the
        # upstream fix's reciprocal multiply. The polynomial figures are the granularity
        # an attack consumes, 256 coefficients per call, with the MDE beside the mean.
        ab = xr.get("per_call_reciprocal_ablation", {}).get("by_n", {})
        if ab.get("recip_n_4000000_mean_ticks") is not None:
            out.append(tex_macro("hostPerCallRecipTicks",
                                 f"{abs(ab['recip_n_4000000_mean_ticks']):.2f}"))
            out.append(tex_macro("hostPerCallRecipT", f"{ab['recip_n_4000000_t']:.0f}"))
            out.append(tex_macro("hostPerCallRecipMde",
                                 f"{ab['recip_n_4000000_mde_ticks']:.3f}"))
        sens = xr.get("per_call_magnitude_sensitivity", {})
        if sens.get("mean_ticks_at_max_n") is not None:
            # The SIGN, spelled, because it carries the finding: the high-magnitude class
            # is the faster one, which no rising operand latency produces.
            out.append(tex_macro("hostPerCallSign",
                                 "faster" if sens["mean_ticks_at_max_n"] < 0 else "slower"))
            out.append(tex_macro("hostPerCallT",
                                 f"{sens.get('by_n', {}).get('n_4000000_t', 0):.0f}"))
            out.append(tex_macro("hostPerCallMde",
                                 f"{sens.get('by_n', {}).get('n_4000000_mde_ticks', 0):.3f}"))
        poly = xr.get("per_polynomial_two_class", {}).get("by_n", {})
        if poly.get("poly_div_n_400000_mean_ticks") is not None:
            out.append(tex_macro("polyDeltaTicks",
                                 f"{abs(poly['poly_div_n_400000_mean_ticks']):.2f}"))
            out.append(tex_macro("polyMdeTicks", f"{poly['poly_div_n_400000_mde_ticks']:.2f}"))
            out.append(tex_macro("polyCallTicks", f"{poly['poly_div_mean_ticks_low']:,.0f}"))
            # The pair count and coefficient count, read from poly_granularity.c's own
            # #defines rather than typed beside them.
            _pg = (REPO / "pairs" / "kyberslash" / "x86" / "poly_granularity.c").read_text()
            _pm = re.search(r"#define PAIRS (\d+)", _pg)
            if _pm:
                out.append(tex_macro("polyPairs", f"{int(_pm.group(1)):,}"))
            _m = re.search(r"#define N (\d+)", _pg)
            if _m:
                out.append(tex_macro("ksPolyCoeffs", _m.group(1)))
            # Re-credit the json record: reading poly_granularity.c above made it the
            # provenance context, but polyMdePercent and every host macro below is read
            # from kyberslash_x86_idiv.json, not the C harness.
            xp.read_text()
            out.append(tex_macro("polyMdePercent",
                                 f"{poly['poly_div_n_400000_mde_ticks'] / poly['poly_div_mean_ticks_low'] * 100:.2f}\\%"))
        else:
            xp.read_text()
        st = xr["kyberslash_operand_range_step"]
        out.append(tex_macro("hostStepTicks", f"{abs(st['step_ticks']):.3f}"))
        out.append(tex_macro("hostNoiseFloor", f"{st['noise_floor_ticks']:.2f}"))
        # The two coefficients the paired boundary design compares, from the record's
        # own key names, so the prose cannot name a different pair than the measurement.
        # The boundary coefficient, parsed from the record's own key name so the prose
        # cannot name a different one than the measurement. Fail loudly on a miss rather
        # than fall back to a literal, so a future rename cannot silently freeze it.
        _bk = re.search(r"_below_(\d+)", json.dumps(st))
        if not _bk:
            raise SystemExit("regen: no _below_<n> key in kyberslash_operand_range_step; "
                             "the boundary coefficient cannot be parsed from the record")
        _blo = int(_bk.group(1))
        out.append(tex_macro("ksBoundaryLo", str(_blo - 1)))
        out.append(tex_macro("ksBoundaryHi", str(_blo)))
        cg = xr["codegen"]["idiv_in_coeff_to_bit"]
        out.append(tex_macro("hostIdivOs", str(cg["Os"])))
        out.append(tex_macro("hostIdivReciprocal", str(cg["O2"])))
        if xr.get("tsc_ghz"):
            out.append(tex_macro("hostTscGHz", f"{xr['tsc_ghz']:.2f}"))
            out.append(tex_macro("hostTickPs", f"{1000.0 / xr['tsc_ghz']:.0f}"))
        # The x86 end-to-end pipelined figures, so the three per-operation quantities in
        # sec/microarch can be told apart: a serial-chain latency with no resolvable step, a
        # per-call two-class step that is resolvable, and a pipelined end-to-end
        # difference that is absorbed. dudect measures the third.
        _xe = xr.get("end_to_end_coeff_to_bit_Os", {})
        if _xe.get("low_coeffs_ticks_per_call"):
            out.append(tex_macro("hostPipelinedCallTicks",
                                 f"{_xe['low_coeffs_ticks_per_call']:.1f}"))
            out.append(tex_macro("hostPipelinedDelta",
                                 f"{abs(_xe['secret_dependent_delta_ticks']):.3f}"))
        # x86 end-to-end two-class delta: the x86 rung of the host-magnitude ladder
        # (I2, the host), against gravDeltaPercent on Neoverse-V1. Distinct from the single-bit
        # step above, which is what I3, the analyser index, rests on.
        e2x = xr.get("end_to_end_coeff_to_bit_Os")
        if e2x and e2x.get("delta_percent_of_call") is not None:
            out.append(tex_macro("hostDeltaTicks", f"{e2x['secret_dependent_delta_ticks']:.3f}"))
            out.append(tex_macro("hostDeltaPercent", f"{e2x['delta_percent_of_call']:.2f}\\%"))
        # Per-call operand-magnitude sensitivity (serialised), the number that shows the
        # x86 step is resolvable per-call but absorbed when pipelined.
        pcs = xr.get("per_call_magnitude_sensitivity")
        if pcs and pcs.get("mean_ticks_at_max_n") is not None:
            out.append(tex_macro("hostPerCallTicks", f"{abs(pcs['mean_ticks_at_max_n']):.2f}"))
    # The turbo-off companion of the x86 record, acquired by the user with the core clock
    # held by the platform's no_turbo switch. The macros exist so the prose can print the
    # two conditions side by side; while the record is absent they expand to NA and the
    # table row to nothing, and regen refuses a record that does not say turbo disabled.
    xto = REPO / "results" / "kyberslash_x86_idiv_turbooff.json"
    _tf = {"hostIdivSpreadTurboOff": None, "hostStepTicksTurboOff": None,
           "hostNoiseFloorTurboOff": None, "hostPerCallTicksTurboOff": None,
           "hostPerCallTTurboOff": None, "hostPerCallRecipTicksTurboOff": None,
           "hostPerCallRecipTTurboOff": None, "hostPipelinedCallTicksTurboOff": None,
           "hostDeltaTicksTurboOff": None, "hostDeltaPercentTurboOff": None,
           "hostTscGHzTurboOff": None}
    _row = ""
    if xto.exists():
        _xd = json.loads(xto.read_text())
        if str(_xd.get("host", {}).get("turbo")) != "disabled":
            raise SystemExit("regen: the turbo-off companion record does not say turbo disabled")
        _x = _xd["results"]
        _st = _x["kyberslash_operand_range_step"]
        _tf["hostIdivSpreadTurboOff"] = f"{_x['idiv_latency_operand_dependent']['spread_ticks']:.3f}"
        _tf["hostStepTicksTurboOff"] = f"{abs(_st['step_ticks']):.3f}"
        _tf["hostNoiseFloorTurboOff"] = f"{_st['noise_floor_ticks']:.2f}"
        _ps = _x.get("per_call_magnitude_sensitivity", {})
        if _ps.get("mean_ticks_at_max_n") is not None:
            _tf["hostPerCallTicksTurboOff"] = f"{abs(_ps['mean_ticks_at_max_n']):.2f}"
            _tf["hostPerCallTTurboOff"] = f"{_ps.get('by_n', {}).get('n_4000000_t', 0):.0f}"
        _ab = _x.get("per_call_reciprocal_ablation", {}).get("by_n", {})
        if _ab.get("recip_n_4000000_mean_ticks") is not None:
            _tf["hostPerCallRecipTicksTurboOff"] = f"{abs(_ab['recip_n_4000000_mean_ticks']):.2f}"
            _tf["hostPerCallRecipTTurboOff"] = f"{_ab['recip_n_4000000_t']:.0f}"
        _xe2 = _x.get("end_to_end_coeff_to_bit_Os", {})
        if _xe2.get("low_coeffs_ticks_per_call"):
            _tf["hostPipelinedCallTicksTurboOff"] = f"{_xe2['low_coeffs_ticks_per_call']:.1f}"
            _tf["hostDeltaTicksTurboOff"] = f"{abs(_xe2['secret_dependent_delta_ticks']):.3f}"
            _tf["hostDeltaPercentTurboOff"] = f"{_xe2['delta_percent_of_call']:.2f}" + chr(92) + "%"
        if _x.get("tsc_ghz"):
            _tf["hostTscGHzTurboOff"] = f"{_x['tsc_ghz']:.2f}"
        _row = (r"\acqHost{}, turbo off & " + str(_tf["hostIdivSpreadTurboOff"]) + " & "
                + str(_tf["hostStepTicksTurboOff"]) + " & " + str(_tf["hostDeltaTicksTurboOff"])
                + " & " + str(_tf["hostDeltaPercentTurboOff"]) + " & "
                + str(_tf["hostNoiseFloorTurboOff"]) + r" \\")
    for _k, _v in _tf.items():
        out.append(tex_macro(_k, _v if _v is not None else chr(92) + "NA"))
    out.append("\\newcommand{\\hostTurboOffRow}{" + _row + "}")
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
        # Where that budget comes from. Every corpus acquisition runs BATCHES batches of
        # MEASUREMENTS measurements (src/corpus/score/adapters/dudect.py), and
        # dudect_run.h writes each batch minus its warm-up records and the last, unfilled
        # slot, dropping any non-positive delta. All three constants are read from the
        # code, and the product is checked against the committed dumps' record count so
        # the paper's explanation of the number cannot drift from the number.
        _ad = (REPO / "src" / "corpus" / "score" / "adapters" / "dudect.py").read_text()
        _rh = (REPO / "src" / "corpus" / "score" / "adapters" / "dudect_run.h").read_text()
        _mb = re.search(r"^BATCHES\s*=\s*(\d+)", _ad, re.M)
        _mm = re.search(r"^MEASUREMENTS\s*=\s*(\d+)", _ad, re.M)
        _mw = re.search(r"for \(size_t i = (\d+); i \+ 1 < M", _rh)
        if _mb and _mm and _mw:
            _b, _m, _w = int(_mb.group(1)), int(_mm.group(1)), int(_mw.group(1))
            _per = _m - _w - 1
            emit("dudectBatches", _b)
            out.append(tex_macro("dudectMeasPerBatch", f"{_m:,}"))
            emit("dudectWarmup", _w)
            # NA rather than a number if the derivation does not reproduce the budget.
            out.append(tex_macro("dudectPerBatch",
                                 f"{_per:,}" if ns and _b * _per == ns[-1] else "\\NA"))
        # The bootstrap behind every class-difference interval, read from
        # bin/dudect_ci.py's defaults: a percentile interval (np.percentile at 2.5 and
        # 97.5 on the resampled differences, no bias correction) over this many draws,
        # each class subsampled to this many per draw, after this upper-tail crop.
        _ci = (REPO / "bin" / "dudect_ci.py").read_text()
        _mboot = re.search(r"boot: int = (\d+), boot_n: int = (\d+)", _ci)
        _mcrop = re.search(r"crop_pct: float = ([\d.]+)", _ci)
        if _mboot:
            out.append(tex_macro("dudectBootDraws", f"{int(_mboot.group(1)):,}"))
            out.append(tex_macro("dudectBootSub", f"{int(_mboot.group(2)):,}"))
        if _mcrop:
            out.append(tex_macro("dudectEffectCrop", f"{float(_mcrop.group(1)):g}"))
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
        # mxTFixedArm and mxTPrefixArm are no longer emitted. The aarch64 figures they
        # carried were acquired five hours before the harness correction that stopped
        # dudect_mx.c timing scalar multiplication on the wrong curve, so they measured
        # a different curve; the block is retired in results/fix_verification.json and
        # the paper no longer claims a cross-host replication of this case.
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
        # mxEffectPrefix is one committed dump (the first acquisition of the pre-fix
        # arm, results/raw/matrixssl/); the other two acquisitions of every design are
        # committed too, under results/raw/matrixssl/repeats/<ver>.<design>.r<n>.bin.gz,
        # and the three-acquisition mean is mxRepPrefixMeanEffect, emitted below.
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

        # The site-closure row each case meets (Definition 4), read from the record so
        # tab:fixes and results/fix_verification.json cannot disagree about it.
        for lib, macro in (("libgcrypt", "fixClosureLibgcrypt"),
                           ("matrixssl", "fixClosureMatrixssl"),
                           ("wolfssl", "fixClosureWolfssl")):
            if fvd["libraries"].get(lib, {}).get("site_closure"):
                out.append(tex_macro(macro, fvd["libraries"][lib]["site_closure"]))
        wolf = fvd["libraries"]["wolfssl"]
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
            # Built and measured is not the same as retained: wolfSSL's arms were
            # built and timed, and no tree, binary or sample survives (retained =
            # false in the record), so the paper says so beside the measured count.
            out.append(tex_macro("nSurveyRetained",
                                 str(sum(1 for v in st.values()
                                         if v.get("measured")
                                         and v.get("retained", True) is not False))))
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
    # assert that its pinned cells reproduce, in a paper whose I1 thesis is that the
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
        _ppdoc = json.loads(ppp.read_text())
        pw = _ppdoc.get("arms", {})
        # Definition 1's constants: size, power and CI level, read from the record the
        # patched-arm power is computed under, so the definition cannot drift from the run.
        _dsg = _ppdoc.get("design")
        if _dsg:
            out.append(tex_macro("mdeAlpha", f"{_dsg['alpha']:g}"))
            out.append(tex_macro("mdePower", f"{_dsg['power']:g}"))
            out.append(tex_macro("ciLevelPct", f"{round(_dsg['ci_level'] * 100):d}\\%"))
        camel = {"ecdsa-nonce": "NonceLatency", "ecdsa-address": "NonceAddress",
                 "hmac-timing": "Hmac", "kyberslash": "Division", "hqc-reject": "Rejection"}
        for pair, suffix in camel.items():
            r = pw.get(pair)
            if not r:
                continue
            out.append(tex_macro("effPatched" + suffix, f"{r['effect_ticks']:,.3f}"))
            out.append(tex_macro("ciHalfPatched" + suffix,
                                 f"{r['ci_half_width_ticks']:,.3f}"))
        # The MDE of every patched arm, per Definition 1, read from the committed dump
        # through bin/dudect_ci.mde at the size and power the design block records, so
        # the table's MDE column and the definition's constants cannot drift apart.
        _alpha = (_dsg or {}).get("alpha", 0.05)
        _power = (_dsg or {}).get("power", 0.8)
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location("dudect_ci", REPO / "bin" / "dudect_ci.py")
            _dci = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_dci)
        except Exception:      # numpy absent: the macros stay undefined, never 0
            _dci = None
        if _dci is not None:
            for pair, suffix in camel.items():
                dump = REPO / "results" / "raw" / f"{pair}_patched.dudect.bin.gz"
                if not dump.exists():
                    continue
                _m = _dci.mde_path(dump, alpha=_alpha, power=_power)
                if _m.get("mde_ticks") is not None:
                    out.append(tex_macro("mdePatched" + suffix, f"{_m['mde_ticks']:,.3f}"))
                    # The division row's MDE against the operand step the x86 micro-
                    # benchmark estimates at the divisor boundary: the ratio the body
                    # quotes when it says this host resolves neither the step nor its
                    # absence. Emitted here so the prose cannot retype it.
                    if pair == "kyberslash" and xp.exists():
                        _st = json.loads(xp.read_text())["results"]
                        _step = abs(_st["kyberslash_operand_range_step"]["step_ticks"])
                        if _step > 0:
                            out.append(tex_macro("mdeStepRatioDivision",
                                                 f"{_m['mde_ticks'] / _step:,.0f}"))
            # The same quantity for the MatrixSSL designs tab:fixes and fig:mxladder
            # draw on, from the committed first-acquisition dumps.
            for macro, dump in (("mxMdeFixed", "mx430_bit255v256"),
                                ("mxMdeControl", "mx430_same"),
                                ("mxMdeSameDigit", "mx430_samedigit"),
                                ("mxMdeDiffDigit", "mx430_diffdigit"),
                                ("mxMdePrefix", "mx4-2-1_bit255v256"),
                                ("mxMdeLatest", "mx4-6-0_bit255v256")):
                path = REPO / "results" / "raw" / "matrixssl" / f"{dump}.bin.gz"
                if not path.exists():
                    continue
                _m = _dci.mde_path(path, alpha=_alpha, power=_power)
                if _m.get("mde_ticks") is not None:
                    out.append(tex_macro(macro, f"{_m['mde_ticks']:,.0f}"))
    # The budget each analyser's clean verdict is conditional on, per tool, for the
    # budget column of tab:blindspot. dudect's is its measurement count (dudectBudget,
    # above). binsec's is the path depth and solver timeout the adapter passed: the
    # per-pair harness value where pairs/<pair>/harness/binsec.toml sets one, else the
    # adapter's own default, read from the adapter source rather than retyped. timecop
    # and varlat record neither a coverage nor an instruction count, so no macro is
    # emitted for them and the table prints "not recorded".
    _ad = REPO / "src" / "corpus" / "score" / "adapters" / "binsec.py"
    if _ad.exists():
        _src = _ad.read_text()
        _dd = re.search(r'cfg\.get\("depth",\s*(\d+)\)', _src)
        _dt = re.search(r'cfg\.get\("sse_timeout",\s*(\d+)\)', _src)
        if _dd and _dt:
            for pair, suffix in (("hmac-timing", "Hmac"), ("kyberslash", "Division"),
                                 ("hqc-reject", "Rejection")):
                hp = REPO / "pairs" / pair / "harness" / "binsec.toml"
                if not hp.exists():
                    continue
                hc = tomllib.loads(hp.read_text())
                out.append(tex_macro("binsecDepth" + suffix,
                                     f"{int(hc.get('depth', _dd.group(1))):,}"))
                out.append(tex_macro("binsecSolver" + suffix,
                                     f"{int(hc.get('sse_timeout', _dt.group(1)))}"))
    # The pinned binsec image's own version string, probed and recorded in
    # data/tools.toml, so the analyser table can cite the release its varlat tick rests on.
    _tt = tomllib.loads((REPO / "data" / "tools.toml").read_text())
    _bv = _tt.get("tool", {}).get("binsec", {}).get("image_version")
    if _bv:
        out.append(tex_macro("binsecImageVersion", str(_bv)))
    # The committed signing trace and the key that labels it. The paper used to mark
    # this group as not recomputable because neither survived the acquisition; both are
    # in the repository now, so the count comes from the file rather than from memory.
    tr = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "trace-4-3-0.csv.z"
    kf = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "signing-key-4-3-0.hex"
    if tr.exists() and kf.exists():
        import zlib as _zlib
        _n = _zlib.decompress(tr.read_bytes()).count(b"\n") - 1   # minus the header line
        out.append(tex_macro("mxTraceN", f"{_n:,}"))
    # The two larger 4-3-0 traces and their labelling keys, committed beside the first;
    # counted from the committed files for the same reason as mxTraceN, so the
    # not-recomputable inventory lists every trace the repository actually holds.
    for _macro, _stem in (("mxTraceNFifty", "4-3-0-50000"),
                          ("mxTraceNHundred", "4-3-0-100000")):
        _trp = (REPO / "pairs" / "matrixssl-minerva" / "evidence"
                / f"trace-{_stem}.csv.z")
        _kfp = (REPO / "pairs" / "matrixssl-minerva" / "evidence"
                / f"signing-key-{_stem}.hex")
        if _trp.exists() and _kfp.exists():
            import zlib as _zlib
            _nn = _zlib.decompress(_trp.read_bytes()).count(b"\n") - 1
            out.append(tex_macro(_macro, f"{_nn:,}"))

    # How many fix-verification designs share a decision. Printed as a word in the
    # statistical appendix, where it drifted the moment the corpus gained two dumps.
    _fvp = REPO / "results" / "fix_verification.json"
    if _fvp.exists():
        _des = (json.loads(_fvp.read_text())["libraries"]["matrixssl"]
                .get("measurements_full_report", {}).get("designs", {}))
        if _des:
            out.append(tex_macro("nFixDesigns", str(len(_des))))
            out.append(tex_macro("nFixDesignsWord",
                                 WORDS[len(_des)] if len(_des) < len(WORDS) else str(len(_des))))

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
        # Two denominators, one per cent apart, and the paper had spent them the wrong
        # way round: harness_overstatement_factor divides by the library's own key
        # generation (genkey), and a sentence whose referent is the deployed call
        # (mulnull) needs the other ratio, computed here from the same record.
        out.append(tex_macro("mxHarnessFactorDeployed",
                             f"{m['mulmod'] / m['mulnull']:.2f}"))
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
        # The effect estimator's post-crop sample size, NOT a record count: the repeat
        # dumps each hold the full corpus budget and matrixssl_report.py crops to its top
        # 95 per cent before the bootstrap, so this is smaller than the acquisition.
        _rn = [r["cropped_sample_size"] for g in rj.values() for r in g.get("per_rep", [])]
        if _rn:
            out.append(tex_macro("mxRepNLo", f"{min(_rn):,}"))
            out.append(tex_macro("mxRepNHi", f"{max(_rn):,}"))
        # The pre-fix arm on the same footing. mxEffectPrefix is the committed single
        # dump (the first of these three acquisitions); a mean beside a single dump
        # reads as a fall the artifact does not support, so the pre-fix mean and its
        # between-acquisition spread are emitted from the same record as the fixed arm's.
        pre = "4-2-1.bit255"
        if pre in rj:
            d = rj[pre]
            out.append(tex_macro("mxRepPrefixMeanEffect",
                                 f"{d['mean_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepPrefixLo", f"{d['min_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepPrefixHi", f"{d['max_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepPrefixReps", str(d["repeats"])))
            out.append(tex_macro("mxRepPrefixExcl",
                                 str(d["reps_with_interval_excluding_zero"])))
        # The latest open release on the same footing, so that "the residual falls once
        # and does not fall again" is a printed range overlapping the first fixed
        # release's and disjoint from the pre-fix one, not a shape read off a bar.
        lat = "4-6-0.bit255"
        if lat in rj:
            d = rj[lat]
            out.append(tex_macro("mxRepLatestMeanEffect",
                                 f"{d['mean_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepLatestLo", f"{d['min_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepLatestHi", f"{d['max_effect_ticks']:,.0f}"))
            out.append(tex_macro("mxRepLatestReps", str(d["repeats"])))
            out.append(tex_macro("mxRepLatestExcl",
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
        for key, macro in (("varlat_yes", "nFieldVarlatYes"), ("varlat_no", "nFieldVarlatNo"),
                           ("branch_yes", "nFieldBranchYes"), ("address_yes", "nFieldAddressYes")):
            if key in am:
                out.append(tex_macro(macro, str(am[key])))
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
        out.append(tex_macro("selMatrixFull",
                             f"{mx['top90_contaminated_full'] * 100:.0f}\\%"))
        out.append(tex_macro("selLibgcrypt",
                             f"{gc['top90_contaminated_full'] * 100:.1f}\\%"))
        # selMatrixMatched and selMatchedN are gone. They came from a matched-budget row
        # on a 6,000-signature 4.2.1 trace for which this repository carries no key, so
        # they could not be regenerated, and the arm they sat beside was mislabelled as
        # the patched build. Both are dropped rather than carried as unregenerable.
    # The END-TO-END basis for the residual, from the committed 25,000-signature 4-3-0
    # trace (results/exploit_budget_matrixssl.json). The site measurement
    # (bin/fix_report.py) times one eccMulmod call, which with the library's own NULL
    # argument is within about one per cent of the library's key generation
    # (results/matrixssl_containment.json, emitted above as mxGenkeyGap), so the two
    # bases are close on this host; the per-signature basis is still emitted separately,
    # labelled with its region, because the comparison against libgcrypt is per
    # signature and that is the only basis on which the two libraries can be compared.
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
    # It reads results/matrixssl_icount.json, the counts in force. It used to read the
    # pair's evidence/instruction_counts.json, whose per_call block was retired as
    # wrong-curve figures, and it would have gone on silently emitting nothing once that
    # block was renamed, which is a number disappearing from the paper without anyone
    # being told. Fail closed instead.
    icp = REPO / "results" / "matrixssl_icount.json"
    if icp.exists():
        pc = json.loads(icp.read_text()).get("per_call", {})
        if "256" not in pc or "255" not in pc:
            raise SystemExit("matrixssl icount: no per-call counts for the residual fraction")
        # The same residual as a fraction of the same region, by the other instrument,
        # named for its region for the same reason.
        out.append(tex_macro("icResidualOfCall",
                             f"{abs(pc['255']['percent_vs_256']):.2f}\\%"))

    # eccMulmodCt is instruction-identical across the two fixed releases (an identical
    # normalised disassembly), a stronger statement than the statistical
    # "indistinguishable" the paper had been making. The evidence file's byte_identity
    # key holds that normalised-disassembly identity and keeps its name, because this
    # block reads it to emit mxCtInsns.
    bcp = REPO / "pairs" / "matrixssl-minerva" / "evidence" / "binary_confirmation.json"
    if bcp.exists():
        _bi = json.loads(bcp.read_text()).get("byte_identity", "")
        _m = re.search(r"same (\d[\d,]*) instructions", _bi)
        if _m and "IDENTICAL" in _bi:
            out.append(tex_macro("mxCtInsns", _m.group(1)))
    # The MatrixSSL recovery attempts. The paper had "recovery pending" where it now has
    # a measurement: nine timing-ordered attempts, none recovering, and the attack's own
    # information accounting saying why.
    mrp = REPO / "results" / "matrixssl_recovery.json"
    if mrp.exists():
        _mr = json.loads(mrp.read_text())
        out.append(tex_macro("mxLatticeAttempts", str(_mr["attempts_total"])))
        out.append(tex_macro("mxLatticeRecovered", str(_mr["recovered"])))
        _b = sorted({a["budget_signatures"] for a in _mr["attempts"]})
        _d = sorted({a["lattice_dimension"] for a in _mr["attempts"] if a["lattice_dimension"]})
        out.append(tex_macro("mxLatticeBudgetLo", f"{min(_b):,}"))
        out.append(tex_macro("mxLatticeBudgetHi", f"{max(_b):,}"))
        out.append(tex_macro("mxLatticeDimLo", str(min(_d))))
        out.append(tex_macro("mxLatticeDimHi", str(max(_d))))
        _i = [a["assumed_information_bits"] for a in _mr["attempts"] if a["assumed_information_bits"]]
        out.append(tex_macro("mxLatticeInfoLo", str(min(_i))))
        out.append(tex_macro("mxLatticeInfoHi", str(max(_i))))
        out.append(tex_macro("mxKeyBits", str(_mr["key_bits"])))
    # The error-tolerant attack's budget, bounded from the measured signal and noise
    # (results/matrixssl_budget_bound.json); an estimate, printed as one.
    mbp = REPO / "results" / "matrixssl_budget_bound.json"
    if mbp.exists():
        _mb = json.loads(mbp.read_text())
        _m, _b = _mb["measured"], _mb["bound"]

        def _sci(x):
            e = int(math.floor(math.log10(x)))
            return f"{x / 10 ** e:.0f}" + chr(92) + "times10^{" + str(e) + "}"
        out.append(tex_macro("mxBudgetSnr", f"{_m['snr']:.2f}"))
        out.append(tex_macro("mxBudgetSignalTicks", f"{_m['signal_ticks']:,.0f}"))
        out.append(tex_macro("mxBudgetNoiseTicks", f"{_m['noise_sd_ticks']:,.0f}"))
        out.append(tex_macro("mxBudgetOracleErr", f"{_b['oracle_error']:.2f}"))
        out.append(tex_macro("mxBudgetSigsOneRound", _sci(_b["rounds"]["1"]["signatures"])))
        out.append(tex_macro("mxBudgetSigsTwoRounds", _sci(_b["rounds"]["2"]["signatures"])))
        out.append(tex_macro("mxBudgetRawUsable", _sci(_b["raw_signatures_for_ladderleak_low"])))
        _la = _mb["ladderleak_anchor"]
        out.append(tex_macro("mxBudgetLadderleakLo", "2^{" + str(_la["signatures_log2_low"]) + "}"))
        out.append(tex_macro("mxBudgetLadderleakHi", "2^{" + str(_la["signatures_log2_high"]) + "}"))
        out.append(tex_macro("mxBudgetLadderleakBits", str(_la["group_bits"])))
        # The depth accounting that actually decides the sweep: credited against
        # observed leading-zero depth in the fastest ninety, at the headline budget.
        _dep = _mr.get("depth", {}).get("100000") or {}
        if _dep.get("observed_mean_leading_zeros_top90") is not None:
            out.append(tex_macro("mxCreditedLz",
                                 f"{_dep['credited_mean_leading_zeros_top90']:.0f}"))
            out.append(tex_macro("mxObservedLz",
                                 f"{_dep['observed_mean_leading_zeros_top90']:.1f}"))

        # The selection purity on the quiet traces, from the same estimator the paper
        # already uses for the committed trace.
        for n, word in ((50000, "Fifty"), (100000, "Hundred")):
            f = REPO / "results" / f"exploit_budget_matrixssl_{n}.json"
            if f.exists():
                _e = json.loads(f.read_text())
                out.append(tex_macro(
                    f"selMatrix{word}K",
                    f"{_e['selection_quality']['top_90']['frac_contaminated_full_length'] * 100:.1f}\\%"))
                out.append(tex_macro(f"aucMatrix{word}K",
                                     f"{_e['auc_time_vs_short_nonce']:.2f}"))

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
            # Against the prior work's library-data budget, minervaSigsLibrary,
            # from the same record rather than a literal.
            out.append(tex_macro("libgcryptVsPriorFactor",
                                 f"{_g['n_star_p1.0'] / rc['real cryptographic library data']:.0f}"))

    # The libgcrypt robustness curve is not monotone at the tested resolution: the
    # half-success rate is met at one subset size and not at the next tested one, so the
    # paper reports the curve pointwise rather than as a "from" threshold, every count
    # and size read from the committed sweep.
    lrp = REPO / "results" / "recovery_robustness_libgcrypt-minerva.json"
    if lrp.exists():
        _lr = sorted(json.loads(lrp.read_text())["results"],
                     key=lambda r: r["num_signatures"])
        _half = [i for i, r in enumerate(_lr)
                 if 2 * r["recovered"] >= r["seeds"] and r["recovered"] < r["seeds"]]
        if _half:
            _i = _half[0]
            out.append(tex_macro("lgRobustHalfRate",
                                 f"{_lr[_i]['recovered']} of {_lr[_i]['seeds']}"))
            out.append(tex_macro("lgRobustHalfSigs",
                                 f"{_lr[_i]['num_signatures']:,}"))
            if _i + 1 < len(_lr):
                out.append(tex_macro("lgRobustNextRate",
                                     f"{_lr[_i + 1]['recovered']} of {_lr[_i + 1]['seeds']}"))
                out.append(tex_macro("lgRobustNextSigs",
                                     f"{_lr[_i + 1]['num_signatures']:,}"))
        _fails = [r["num_signatures"] for r in _lr if r["recovered"] == 0]
        if _fails:
            out.append(tex_macro("lgRobustNoneSigs", f"{max(_fails):,}"))

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
        # How close "the same number" actually is. The paper had said "the same
        # number" of two figures differing by 539 instructions, which is a claim a
        # reader can falsify by dividing the two macros beside it.
        if "255" in pc and "193" in pc:
            a, b = (abs(pc[k]["delta_vs_256"]) for k in ("255", "193"))
            out.append(tex_macro("icDeltaSpreadPercent", f"{abs(b - a) / b * 100:.1f}\\%"))
        # The counter, named, and the spread as instructions and as ticks: 1% of 53,157 is
        # a few hundred instructions, a few tens of ticks, against a 72,000-tick difference.
        _icd = json.loads(icp.read_text())
        out.append(tex_macro("icCounter", str(_icd.get("method", "")).split(" ")[0]))
        if "255" in pc and "193" in pc and _icd.get("instructions_per_tick"):
            _sp = abs(abs(pc["193"]["delta_vs_256"]) - abs(pc["255"]["delta_vs_256"]))
            out.append(tex_macro("icDeltaSpreadInstr", f"{_sp:,.0f}"))
            out.append(tex_macro("icDeltaSpreadTicks", f"{_sp / _icd['instructions_per_tick']:.0f}"))
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
        # The paper says these pairs DISCRIMINATE at factor one, which is both arms.
        # The macro used to count the vulnerable half only, so the prose claimed more
        # than the emitter computed. Fail closed rather than fall back to the weaker
        # list, because falling back is how the two came apart.
        if "pairs_discriminating_at_factor_one" not in dca:
            raise SystemExit("detection curve: no discrimination list; re-run "
                             "bin/detection_curve_all.py or backfill it")
        out.append(tex_macro("nCurveDetectAtOne",
                             str(len(dca["pairs_discriminating_at_factor_one"]))))
        by = {(r["pair"], r["amp"]): r for r in dca["rows"]
              if r.get("status") and r["arm"] == "vulnerable"}
        for pair, macro in (("kyberslash", "Division"), ("hqc-reject", "Rejection"),
                            ("hmac-timing", "Hmac"), ("ecdsa-nonce", "NonceLatency")):
            # The VERDICT statistic, never dudect's own max over every test. The two
            # differ by more than a rounding: on the amplified message arm they read
            # 213 and 1901, unamplified 138 and 220, and "climbs steeply" was a property of the
            # wrong one. Fail closed rather than fall back, because a fallback here
            # is how the wrong statistic got printed in the first place.
            ts = [by[(pair, a)]["permutation_max_abs_t"] for a in (1, 2, 4, 8)
                  if (pair, a) in by]
            if any(v is None for v in ts):
                raise SystemExit(f"detection curve: {pair} has a row with no verdict "
                                 f"statistic; run bin/detection_curve_all.py --backfill")
            if len(ts) == 4:
                out.append(tex_macro(f"curveOne{macro}", f"{ts[0]:.0f}"))
                out.append(tex_macro(f"curveEight{macro}", f"{ts[-1]:.0f}"))
            # The other statistic, printed once beside the first so the paper can say
            # they are not interchangeable without the reader taking that on trust.
            if pair == "hmac-timing" and (pair, 8) in by:
                out.append(tex_macro("dudectOwnMaxHmac",
                                     f"{by[(pair, 8)]['dudect_max_t']:.0f}"))
        # The one disclosed row where a patched arm's own null rejects at a single
        # factor: its p, effect and CI, printed rather than characterised, and the
        # run count so the reader can see it is one draw of many.
        import re as _re
        out.append(tex_macro("nCurveRuns", str(len(dca["rows"]))))
        _pat = [r for r in dca["rows"] if r["pair"] == "hqc-reject"
                and r["arm"] == "patched"]
        _leak = [r for r in _pat if r["status"] == "leak_reported"]
        if len(_leak) == 1:
            _r = _leak[0]
            out.append(tex_macro("hqcPatchedLeakFactor", str(_r["amp"])))
            out.append(tex_macro("hqcPatchedLeakP", f"{_r['permutation_p']:.4f}"))
            _m = _re.search(r"effect ([\d.]+) ticks, 95% CI \[([\d.]+), ([\d.]+)\]",
                            str(_r.get("detail", "")))
            if _m:
                out.append(tex_macro("hqcPatchedLeakEffect", f"{float(_m.group(1)):.1f}"))
                out.append(tex_macro("hqcPatchedLeakCILo", f"{float(_m.group(2)):.1f}"))
                out.append(tex_macro("hqcPatchedLeakCIHi", f"{float(_m.group(3)):.1f}"))
            _clean = sorted(r["amp"] for r in _pat if r["status"] == "clean")
            _cleanp = {r["amp"]: r["permutation_p"] for r in _pat if r["status"] == "clean"}
            out.append(tex_macro("hqcPatchedCleanFactors",
                                 ", ".join(str(a) for a in _clean[:-1]) + f" and {_clean[-1]}"))
            out.append(tex_macro("hqcPatchedCleanPs",
                                 ", ".join(f"{_cleanp[a]:.2f}" for a in _clean)))
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
    _prov.use("census")
    emit("nCensusIncluded", cen["census_included"])
    emit("nCensusExcluded", cen["census_excluded"])
    _prov.use("cost")
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
        erec = json.loads(ep.read_text())
        cells = erec.get("emission_map", [])
        leaking = sum(1 for c in cells if c.get("leak_emitted"))
        emit("nEmissionCells", len(cells))
        emit("nLeakingCells", leaking)
        emit("nConstantTimeCells", len(cells) - leaking)
        # The optimisation settings the locked map spans, from the generator's own
        # level list; falls back to the distinct labels for a record written before
        # the generator existed.
        levels = erec.get("levels") or sorted({c.get("opt") for c in cells})
        emit("nEmissionLevels", len(levels))
        emit("nLevelsUnsafeUnderBoth", len(erec.get("levels_unsafe_under_both", [])))

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
    ap.add_argument("--provenance", metavar="PATH", nargs="?",
                    const=str(REPO / "paper" / "tches" / "gen" / "provenance-table.tex"),
                    help="write the table mapping every macro to the emitter line and "
                         "the committed record it was read from (default: the eprint's "
                         "gen/provenance-table.tex); pass - to print it")
    args = ap.parse_args()

    if args.provenance:
        _prov.install()

    def _section(name, fn):
        _prov.section = name
        try:
            return fn()
        finally:
            _prov.section = None

    report = {
        "corpus": _section("corpus", corpus_section),
        "census": _section("census", census_section),
        "verdicts": _section("verdicts", verdict_section),
        "cost": _section("cost", cost_section),
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

    if args.provenance:
        if not args.tex:
            as_tex(report)   # emit every macro so each is attributed; nothing is written
        table = _prov.table()
        if args.provenance == "-":
            sys.stdout.write(table)
        else:
            out = Path(args.provenance)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(table, encoding="utf-8")
            print(f"regen: wrote {out} ({len(_prov.rows)} macros attributed)")

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
