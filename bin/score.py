#!/usr/bin/env python3
"""Score installed analysers over the corpus and report recall per leak class.

This is the number the whole project exists to produce. For each (tool, pair,
arm) the adapter emits a normalised verdict; applicability is computed from the
tool's declared capabilities against the pair's class; and recall is the fraction
of applicable, recall-eligible vulnerable arms on which the tool reports a leak
that discriminates from the patched arm.

Every step that could inflate the number is guarded:
  - inapplicable pairs are excluded from the denominator, not counted as misses
  - a tool that flags the patched arm too is non-discriminating, neither a hit
    nor a clean miss, and is reported as its own count
  - budget_exhausted and error are printed, never silently folded into clean
  - recall is per named class with its n, never a single aggregate percentage
  - tier C pairs never enter a denominator

Usage: bin/score.py [--json]
Exit codes: 0 scored, 2 could not run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def load_adapter(name: str):
    spec = importlib.util.spec_from_file_location(
        f"adapter_{name}", REPO / "src" / "corpus" / "score" / "adapters" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# The four rows the threat appendix singles out: varlat and binsec on the two
# OpenSSL-linked ECDSA pairs. Both tools declare the secret-branch mechanism those
# pairs exhibit, so the missing harness is not an effort boundary of this artifact:
# the reason was measured rather than assumed, and it is that neither pinned image
# can build an OpenSSL-linked arm, varlat's carrying libcrypto but no development
# headers and binsec's shipping no toolchain at all. The probe is recorded in
# results/tool_reach_limits.json. Keying the reason here keeps --rescore
# reproducing the committed wording for these rows instead of reverting them to
# the generic effort-boundary string.
MEASURED_NO_BUILD = {
    ("varlat", "ecdsa-nonce"), ("varlat", "ecdsa-address"),
    ("binsec", "ecdsa-nonce"), ("binsec", "ecdsa-address"),
}
MEASURED_NO_BUILD_REASON = (
    "no harness built here because the tool's pinned image cannot build the pair's "
    "OpenSSL-linked arm (a measured incapacity of the pinned image, recorded in "
    "results/tool_reach_limits.json, not an effort boundary)")


def applicable(tool: dict, pair_mechanisms: list, has_harness: bool,
               has_source: bool = False, tool_name: str = "",
               pair_name: str = "") -> tuple[bool, str]:
    """Compute applicability from mechanism, not from the attacker's channel.

    A pair's `observable` is what an attacker measures; it is not what an
    analyser reads. dudect (timing) and timecop (taint) both detect a
    secret-dependent branch, through different lenses, so applicability keys on
    the mechanism the pair exhibits against the mechanisms the tool detects.

    A pair with no analyser-detectable mechanism (a pure timing-observation set,
    with no runnable program) is inapplicable to a tool that needs to run code.
    """
    detects = set(tool.get("detects_mechanisms", []))
    mech = set(pair_mechanisms)
    if not mech:
        return False, "pair exhibits no mechanism a code-running analyser detects (constant-time control, or observation-only)"
    if not (mech & detects):
        return False, f"mechanism: tool detects {sorted(detects)}, pair exhibits {sorted(mech)}"
    if not has_harness:
        # Distinguish "there is no program to run" from "there is a program but we
        # built no harness for this tool". The first is a property of the pair, the
        # second is an effort boundary of ours, and reporting the second as the first
        # misattributes our own gap to the corpus. A third case is neither: for the
        # (tool, pair) rows in MEASURED_NO_BUILD the gap was probed rather than
        # assumed, and the reason says so instead of calling it an effort boundary.
        if (tool_name, pair_name) in MEASURED_NO_BUILD:
            return False, MEASURED_NO_BUILD_REASON
        if has_source:
            return False, ("no harness built here for this tool, though the pair ships "
                           "runnable source (an effort boundary, not a property of the pair)")
        return False, "no runnable program for this pair (scored on recorded observations)"
    return True, ""


def _reason_for(tools: dict, tool_name: str, pair_name: str) -> str | None:
    """The applicability reason the scoring loop would record for (tool, pair) now.

    Recomputed from the manifest and the tool declaration alone, so --rescore can
    refresh a committed reason without running any analyser. Returns None when the
    pair or tool no longer exists, or when the row would be applicable.
    """
    tool = tools.get(tool_name)
    pair = REPO / "pairs" / pair_name
    if tool is None or not (pair / "pair.toml").exists():
        return None
    man = tomllib.loads((pair / "pair.toml").read_text())
    mech = man["class"].get("mechanism_classes", [])
    harness_cfg = pair / "harness" / f"{tool_name}.toml"
    has_source = any((pair / "src").glob("*.c"))
    has_harness = harness_cfg.exists() and has_source
    ok, reason = applicable(tool, mech, has_harness, has_source, tool_name, pair_name)
    return None if ok else reason


FDR = 0.05


def _apply_bh_to_dudect(rows: list[dict], q: float = FDR) -> None:
    """Downgrade any dudect arm whose uncorrected p does not survive BH control.

    Only downgrades. An arm the per-run rule already called clean is never promoted
    by a multiplicity correction, and an arm it called a leak becomes clean only
    because the family says that p is the expected borderline result rather than a
    finding. Every downgrade is recorded in the row so it is visible, not silent.
    """
    fam = []
    for r in rows:
        if r.get("tool") != "dudect":
            continue
        for who in ("vulnerable", "patched"):
            pv = r.get(f"{who}_permutation_p")
            if pv is not None:
                fam.append((pv, r, who))
    if not fam:
        return
    fam.sort(key=lambda x: x[0])
    m = len(fam)
    k = 0
    for i, (pv, _, _) in enumerate(fam, start=1):
        if pv <= i * q / m:
            k = i
    for i, (pv, r, who) in enumerate(fam, start=1):
        if i > k and r.get(f"{who}_status") == "leak_reported":
            r[f"{who}_status"] = "clean"
            r.setdefault("bh_downgraded", []).append(
                f"{who} (uncorrected p={pv:.4f} does not survive BH at FDR {q} "
                f"over {m} dudect arms)")


def _facet_names() -> set[str]:
    """The class facets, from the vocabulary that defines them."""
    c = tomllib.loads((REPO / "data" / "classes.toml").read_text())
    return set(c.get("facet", {}))


FACET_NAMES = _facet_names()


UNRESOLVED = ("budget_exhausted", "error", "inconclusive")


def decide(vuln_status: str, patched_status: str) -> str:
    """The outcome rule, as a pure function of the two arm statuses.

    Factored out so that --rescore applies exactly the rule a fresh run applies. It
    was inline once, and when the rule changed the committed rows kept the outcome
    the old rule gave: a grounded audit found binsec/hqc-reject still recorded as a
    detection under a rule that had already been changed to refuse one.

    A detection requires the patched arm to be RESOLVED clean, not merely "not red".
    An unresolved patched arm cannot underwrite a discrimination: the tool may simply
    not have run long enough to flag it, and counting that as a detection inflates
    recall.
    """
    hit, fp = vuln_status == "leak_reported", patched_status == "leak_reported"
    if hit and patched_status in UNRESOLVED:
        return "inconclusive"
    if hit and not fp:
        return "detected"              # red on the bug, green on the fix
    if hit and fp:
        return "non_discriminating"    # flags both arms
    if vuln_status in UNRESOLVED:
        return vuln_status
    return "missed"


def adjudicate(outcome: str, tier: str | None, technique: str | None) -> str:
    """Apply the site-local adjudication rule to a tier-C miss by a host-bound tool.

    A statistical timing tool's verdict is a proposition about the host and budget
    it ran on. A tier-C pair's label was certified by a published exploit on a host
    this artifact did not measure, so a clean reading here does not contradict that
    label and cannot be scored against it as a miss: it is unadjudicated, the same
    status Section 6.1 gives a flag away from the certified site. Added 2026-09-02
    after the fifteenth panel round; nothing numeric moves, because tier C enters
    no denominator, but the table no longer calls a verdict the paper says is
    correct a miss.
    """
    if outcome == "missed" and tier == "C" and technique == "statistical":
        return "unadjudicated"
    return outcome


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--recall-only", action="store_true",
                    help="recompute recall (exploit and policy) from committed "
                         "verdicts.jsonl, running no adapters. The policy metric is a "
                         "re-reading of the same observations, not a new measurement.")
    ap.add_argument("--pair", help="score only this pair and MERGE its rows into "
                    "verdicts.jsonl, leaving the other pairs' committed rows untouched "
                    "(the existing statistical rows are the sealed pilot values).")
    ap.add_argument("--tool", help="score only this tool across all pairs and MERGE "
                    "its rows, leaving the other tools' committed rows untouched (used "
                    "to re-acquire dudect under the PR-3 verdict rule without disturbing "
                    "the deterministic taint and symbolic rows).")
    ap.add_argument("--arms", default="vulnerable,patched",
                    help="with --pair: which arms to RUN the adapters on (comma list). The "
                         "other arm's statuses are taken from its committed row, so a change "
                         "to one arm's source (the patched arm becoming upstream's real fix) "
                         "does not re-acquire the other arm's dump and move its numbers for "
                         "no reason. Every row this produces records which arms were run.")
    ap.add_argument("--rescore", action="store_true",
                    help="re-derive every committed outcome from its committed arm "
                         "statuses under the rule now in force, running no analyser. "
                         "The statuses are what the adapters observed; the outcome is a "
                         "pure function of them, so when the rule changes this is how "
                         "the committed rows catch up.")
    a = ap.parse_args()

    if a.rescore:
        vp = REPO / "results" / "verdicts.jsonl"
        rows = [json.loads(l) for l in vp.read_text().splitlines() if l.strip()]
        tools = tomllib.loads((REPO / "data" / "tools.toml").read_text())["tool"]
        changed = []
        for r in rows:
            v, pt = r.get("vulnerable_status"), r.get("patched_status")
            if r.get("applicable") is False:
                # An inapplicable row's reason is also a pure function of the manifest
                # and the tool declaration, so it is refreshed here too. Six rows once
                # carried a reason string this scorer no longer emits, and the only
                # thing that noticed was a tolerant reader in bin/regen.py that
                # accepted both spellings, which is how the drift stayed hidden.
                want = _reason_for(tools, r["tool"], r["pair"])
                if want is not None and want != r.get("reason"):
                    changed.append((r["tool"], r["pair"], "reason", "refreshed"))
                    r["reason"] = want
                continue
            if not r.get("applicable") or v is None or pt is None:
                continue
            want = adjudicate(decide(v, pt), r.get("tier"), tools.get(r["tool"], {}).get("technique"))
            if want != r.get("outcome"):
                changed.append((r["tool"], r["pair"], r["outcome"], want))
                r["outcome"] = want
        vp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        for tool, pair, was, now in changed:
            print(f"rescore: {tool}/{pair} {was} -> {now}")
        print(f"rescore: {len(changed)} row(s) changed of {len(rows)}")
        return 0

    tools = tomllib.loads((REPO / "data" / "tools.toml").read_text())["tool"]
    pairs = sorted(p.parent for p in (REPO / "pairs").glob("*/pair.toml"))

    rows = []
    if a.recall_only:
        rows = [json.loads(l) for l
                in (REPO / "results" / "verdicts.jsonl").read_text().splitlines()
                if l.strip()]
    for tool_name, tool in tools.items():
        if a.recall_only:
            break
        if a.tool and tool_name != a.tool:
            continue
        adapter = load_adapter(tool_name)
        for pair in pairs:
            if a.pair and pair.name != a.pair:
                continue
            man = tomllib.loads((pair / "pair.toml").read_text())
            role = man["pair"].get("role")
            tier = man["pair"].get("tier")
            if role == "fix-case":
                # A deployed-library fix case (pairs/matrixssl-minerva) is graded at its
                # fix site by the fix-verification instrument, not by the analyser grid.
                # It carries no analyser row in this revision, so it enters neither the
                # applicability grid nor any denominator; skipping it here is what keeps
                # the scored-item and corpus counts unchanged by its manifest.
                continue
            # Allowlist from the closed vocabulary, never "all keys except a few".
            # The denylist form silently promotes any new [class] field to a facet,
            # which is how the census join broke once already; recall grouping would
            # break the same way, and just as quietly.
            cls = {k: v for k, v in man["class"].items() if k in FACET_NAMES}
            mech = man["class"].get("mechanism_classes", [])
            # A pair is runnable by this tool if it ships source and a config for
            # this tool's harness family.
            harness_cfg = pair / "harness" / f"{tool_name}.toml"
            has_source = any((pair / "src").glob("*.c"))
            has_harness = harness_cfg.exists() and has_source

            ok, reason = applicable(tool, mech, has_harness, has_source,
                                    tool_name, pair.name)
            row = {"tool": tool_name, "pair": pair.name, "role": role,
                   "tier": tier, "class": cls}
            if not ok:
                row.update({"applicable": False, "reason": reason})
                rows.append(row)
                continue

            # Run the adapter on the requested arms; reuse the committed row for the
            # rest. A reused arm is reconstructed from the committed fields so the
            # merge below sees a complete row, and the row says which arms ran.
            run_arms = [x.strip() for x in a.arms.split(",") if x.strip()]
            committed_row = None
            if set(run_arms) != {"vulnerable", "patched"}:
                vp = REPO / "results" / "verdicts.jsonl"
                for l in vp.read_text().splitlines():
                    if not l.strip():
                        continue
                    r0 = json.loads(l)
                    if r0.get("pair") == pair.name and r0.get("tool") == tool_name:
                        committed_row = r0
                if committed_row is None:
                    raise SystemExit(f"--arms: no committed row for {tool_name}/{pair.name} "
                                     f"to reuse; run both arms")

            def reuse(who):
                r0 = committed_row
                return {"status": r0.get(f"{who}_status"), "max_t": r0.get(f"{who}_max_t"),
                        "max_tau": r0.get(f"{who}_max_tau"),
                        "effect_ticks": r0.get(f"{who}_effect_ticks"),
                        "ci_low": (r0.get(f"{who}_ci") or [None, None])[0],
                        "ci_high": (r0.get(f"{who}_ci") or [None, None])[1],
                        "raw": r0.get(f"{who}_raw"),
                        "permutation_p": r0.get(f"{who}_permutation_p")}

            vuln = adapter.score(pair, "vulnerable") if "vulnerable" in run_arms else reuse("vulnerable")
            patch = adapter.score(pair, "patched") if "patched" in run_arms else reuse("patched")
            if committed_row is not None:
                row["arms_run"] = run_arms
                row["arms_reused_from_committed_row"] = [x for x in ("vulnerable", "patched") if x not in run_arms]
            outcome = adjudicate(decide(vuln["status"], patch["status"]), tier, tool.get("technique"))
            row.update({"applicable": True, "outcome": outcome,
                        "vulnerable_status": vuln["status"],
                        "patched_status": patch["status"],
                        "vulnerable_max_t": vuln.get("max_t"),
                        "patched_max_t": patch.get("max_t")})
            # dudect also reports tau (a REPORTED effect size under PR-4, deciding
            # nothing), the effect in ticks with a bootstrap CI, and the permutation
            # p-value its verdict rests on; carry them so the paper can quote a
            # magnitude and a reader can re-decide without re-measuring.
            for who, res in (("vulnerable", vuln), ("patched", patch)):
                if res.get("max_tau") is not None:
                    row[f"{who}_max_tau"] = res.get("max_tau")
                    row[f"{who}_effect_ticks"] = res.get("effect_ticks")
                    row[f"{who}_ci"] = [res.get("ci_low"), res.get("ci_high")]
                    if res.get("raw"):
                        row[f"{who}_raw"] = res.get("raw")
                if res.get("permutation_p") is not None:
                    row[f"{who}_permutation_p"] = res.get("permutation_p")
            rows.append(row)

    # Multiplicity across the family the corpus actually decides at once. Each
    # adapter sees one run and can only report an uncorrected p; the corpus decides
    # many arms together, so over eighteen arms a borderline uncorrected p is the
    # expected count when nothing is there. Benjamini-Hochberg over every dudect arm
    # is therefore applied HERE, where the family is visible, and it is what promotes
    # an uncorrected call to a reported verdict. Registered in PR-4.
    _apply_bh_to_dudect(rows)

    # With --pair, keep every other pair's committed rows (the sealed pilot
    # statistics) and replace only this pair's, so recall below is computed over the
    # merged corpus without re-perturbing the existing statistical verdicts.
    if (a.pair or a.tool) and not a.recall_only:
        existing = [json.loads(l) for l
                    in (REPO / "results" / "verdicts.jsonl").read_text().splitlines()
                    if l.strip()]
        # Replace exactly the cells this run rescored. With both filters that is one
        # (tool, pair) cell: dropping every row of the tool, as an earlier revision
        # did, would delete that tool's other committed rows and silently shrink the
        # matrix.
        if a.tool and a.pair:
            rows = [r for r in existing
                    if not (r.get("tool") == a.tool and r.get("pair") == a.pair)] + rows
        elif a.tool:
            rows = [r for r in existing if r.get("tool") != a.tool] + rows
        else:
            rows = [r for r in existing if r.get("pair") != a.pair] + rows

    # Recall per (tool, class) over applicable recall-eligible corpus pairs, and
    # the tier-C detections that inform the crossover but never a denominator.
    from collections import defaultdict
    denom = defaultdict(list)
    tier_c = []
    for r in rows:
        if not r.get("applicable") or r["role"] != "corpus":
            continue
        if r["tier"] in ("A", "B"):
            key = (r["tool"], "/".join(f"{k}={v}" for k, v in sorted(r["class"].items())))
            denom[key].append((r["pair"], r["outcome"]))
        elif r["tier"] == "C":
            tier_c.append({"tool": r["tool"], "pair": r["pair"], "outcome": r["outcome"]})

    recall = []
    for (tool, cls), pair_outcomes in sorted(denom.items()):
        hits = sum(1 for _, o in pair_outcomes if o == "detected")
        recall.append({"tool": tool, "class": cls,
                       "detected": hits, "n": len(pair_outcomes),
                       "recall": f"{hits}/{len(pair_outcomes)}",
                       "outcomes": [[p, o] for p, o in pair_outcomes]})
    tier_c.sort(key=lambda d: (d["pair"], d["tool"]))

    # Policy recall (PR-2). A policy tool detects the policy violation on the
    # vulnerable arm whenever it reports a leak there, independently of the patched
    # arm, because the corpus does not certify the patched arm constant-time. This
    # separates a policy tool's real detection from the discrimination metric, so a
    # tool that also flags an uncertified patched arm is not scored a bare failure.
    scored = {t: tools[t].get("scored_against", "exploit") for t in tools}
    pol_denom = defaultdict(list)
    cross = []
    for r in rows:
        if (not r.get("applicable") or r.get("role") != "corpus"
                or r.get("tier") not in ("A", "B")):
            continue
        cls_s = "/".join(f"{k}={v}" for k, v in sorted(r["class"].items()))
        vuln_leak = r.get("vulnerable_status") == "leak_reported"
        cross.append({"tool": r["tool"], "pair": r["pair"],
                      "scored_against": scored.get(r["tool"], "exploit"),
                      "exploit_discriminates": r.get("outcome") == "detected",
                      "policy_detects_vulnerable": vuln_leak,
                      "flags_uncertified_patched_arm":
                          r.get("patched_status") == "leak_reported"})
        if scored.get(r["tool"]) == "policy":
            pol_denom[(r["tool"], cls_s)].append((r["pair"], vuln_leak))
    policy_recall = []
    for (tool, cls), pv in sorted(pol_denom.items()):
        hits = sum(1 for _, v in pv if v)
        policy_recall.append({"tool": tool, "class": cls, "detected": hits,
                              "n": len(pv), "recall": f"{hits}/{len(pv)}",
                              "outcomes": [[p, "policy-detected" if v else "policy-clean"]
                                           for p, v in pv]})
    cross.sort(key=lambda d: (d["pair"], d["tool"]))

    # Policy precision (PR-3): a general false-positive rate over certified
    # constant-time negatives. A flag on proven-CT code is a genuine false positive,
    # unlike a flag on a patched arm, which is only site-local. A tool that errors and
    # cannot analyse a function is excluded, not counted as clean or as a flag.
    prec_denom = defaultdict(list)
    for r in rows:
        if r.get("role") != "certified-negative" or not r.get("applicable"):
            continue
        if r.get("vulnerable_status") == "error":
            continue
        flagged = (r.get("vulnerable_status") == "leak_reported"
                   or r.get("patched_status") == "leak_reported")
        prec_denom[r["tool"]].append((r["pair"], flagged))
    policy_precision = []
    for tool, pf in sorted(prec_denom.items()):
        fp = sum(1 for _, f in pf if f)
        n = len(pf)
        policy_precision.append({"tool": tool, "false_positives": fp, "n": n,
                                 "precision": f"{n - fp}/{n}",
                                 "certified_negatives": [p for p, _ in pf]})

    report = {"rows": rows, "recall_per_class": recall,
              "tier_c_detections": tier_c,
              "note": "recall over applicable, recall-eligible (tier A or B) corpus "
                      "pairs only; sentinels, tier C, and inapplicable pairs excluded"}

    (REPO / "results" / "verdicts.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    # Refresh the round record's numeric fields in place, keeping the curated
    # prose. recall.json is what bin/regen.py reads for the per-class and tier-C
    # macros, so it must regenerate from the same run rather than drift by hand.
    rpath = REPO / "results" / "recall.json"
    doc = json.loads(rpath.read_text()) if rpath.exists() else {}
    doc.setdefault("round", "PR-1")
    doc.setdefault("supersedes_pilot", True)
    doc["recall_per_class"] = recall
    doc["exploit_recall_note"] = ("recall_per_class is exploit recall: red on the "
                                  "vulnerable arm and clean on the patched arm.")
    doc["policy_recall_per_class"] = policy_recall
    doc["cross_table"] = cross
    doc["policy_precision"] = policy_precision
    doc["policy_precision_note"] = ("PR-3. A general false-positive rate over certified "
                                    "constant-time negatives (formally verified code), "
                                    "kept separate from the site-local patched-arm count "
                                    "and from every recall denominator. A tool that "
                                    "errors and cannot analyse a function is excluded.")
    doc["policy_recall_note"] = ("PR-2. A policy tool is scored on whether it flags the "
                                 "policy violation on the vulnerable arm, not on "
                                 "discriminating an uncertified patched arm. timecop's "
                                 "exploit recall on the nonce pairs is 0/1 because it "
                                 "flags both arms, but its policy recall is 1/1 because "
                                 "it correctly reports the secret-dependent operation on "
                                 "the vulnerable arm; the patched-arm flag is the "
                                 "unadjudicated site-local false positive of the threats "
                                 "section, not a discrimination failure.")
    doc["tier_c_detections"] = tier_c
    # The crossover summary is DERIVED, never curated. A hand-written version of this
    # drifted out of agreement with the very fields beside it (it claimed detections on
    # pairs the rows record as non-discriminating), which is the drift the number gate
    # exists to prevent, so it is regenerated from the rows on every run.
    doc.pop("crossover_finding", None)
    by_tool = {}
    for r in rows:
        if not r.get("applicable") or r.get("role") != "corpus":
            continue
        by_tool.setdefault(r["tool"], {}).setdefault(r["outcome"], []).append(
            f"{r['pair']}(tier {r['tier']})")
    doc["crossover_summary"] = {
        t: {o: sorted(ps) for o, ps in sorted(outs.items())}
        for t, outs in sorted(by_tool.items())}
    doc["crossover_summary_note"] = (
        "Derived from verdicts.jsonl on the run that wrote this file: for each tool, "
        "the applicable corpus pairs grouped by outcome, with each pair's tier. Tier C "
        "outcomes are recorded detections and enter no recall denominator.")
    rpath.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    if a.json:
        print(json.dumps(report, indent=2))
    else:
        print("=== per (tool, pair) ===")
        for r in rows:
            if not r.get("applicable"):
                print(f"  {r['tool']:<8} {r['pair']:<22} INAPPLICABLE  {r['reason']}")
            else:
                print(f"  {r['tool']:<8} {r['pair']:<22} {r['outcome']:<18} "
                      f"vuln={r['vulnerable_status']} patched={r['patched_status']}")
        print("\n=== recall per class (applicable, tier A/B corpus pairs) ===")
        if not recall:
            print("  none yet: no applicable recall-eligible pair for any tool")
        for r in recall:
            print(f"  {r['tool']:<8} {r['recall']:<6} {r['class']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
