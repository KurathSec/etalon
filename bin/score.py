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


def applicable(tool: dict, pair_mechanisms: list, has_harness: bool) -> tuple[bool, str]:
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
        return False, "no runnable harness for this pair (scored on recorded observations)"
    return True, ""


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
    a = ap.parse_args()

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
        adapter = load_adapter(tool_name)
        for pair in pairs:
            if a.pair and pair.name != a.pair:
                continue
            man = tomllib.loads((pair / "pair.toml").read_text())
            role = man["pair"].get("role")
            tier = man["pair"].get("tier")
            cls = {k: v for k, v in man["class"].items()
                   if k not in ("rationale", "mechanism_classes")}
            mech = man["class"].get("mechanism_classes", [])
            # A pair is runnable by this tool if it ships source and a config for
            # this tool's harness family.
            harness_cfg = pair / "harness" / f"{tool_name}.toml"
            has_harness = harness_cfg.exists() and any((pair / "src").glob("*.c"))

            ok, reason = applicable(tool, mech, has_harness)
            row = {"tool": tool_name, "pair": pair.name, "role": role,
                   "tier": tier, "class": cls}
            if not ok:
                row.update({"applicable": False, "reason": reason})
                rows.append(row)
                continue

            # Run the adapter on both arms.
            vuln = adapter.score(pair, "vulnerable")
            patch = adapter.score(pair, "patched")
            hit = vuln["status"] == "leak_reported"
            fp = patch["status"] == "leak_reported"
            if hit and not fp:
                outcome = "detected"        # red on the bug, green on the fix
            elif hit and fp:
                outcome = "non_discriminating"  # flags both arms
            elif vuln["status"] in ("budget_exhausted", "error"):
                outcome = vuln["status"]
            else:
                outcome = "missed"
            row.update({"applicable": True, "outcome": outcome,
                        "vulnerable_status": vuln["status"],
                        "patched_status": patch["status"],
                        "vulnerable_max_t": vuln.get("max_t"),
                        "patched_max_t": patch.get("max_t")})
            rows.append(row)

    # With --pair, keep every other pair's committed rows (the sealed pilot
    # statistics) and replace only this pair's, so recall below is computed over the
    # merged corpus without re-perturbing the existing statistical verdicts.
    if a.pair and not a.recall_only:
        existing = [json.loads(l) for l
                    in (REPO / "results" / "verdicts.jsonl").read_text().splitlines()
                    if l.strip()]
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
