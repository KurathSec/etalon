#!/usr/bin/env python3
"""THE ORACLE. Runs every pair's recovery against its published verifier.

This is the deliverable a reader runs, and the constraint that shapes it is that
it must work from a cold clone with a stock interpreter: no containers, no
analysers, no hardware, no network. If this ever needs any of those, the
acquisition and verification halves have leaked into each other and the design
has failed.

Two checks per pair, and the second is the one that matters:

  ORC-1  the recovery succeeds on the vulnerable arm
  ORC-2  the SAME recovery FAILS on the patched arm

Without ORC-2 a corpus cannot distinguish a working key recovery from a script
that already knows the answer, and that objection would end the paper. A pair
that cannot demonstrate the failure is not a pair.

Usage:  bin/verify.py [--pair NAME] [--json]
Exit codes: 0 all pairs verified, 1 a check failed, 2 could not run.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent


def load_module(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_pair(pair_dir: pathlib.Path) -> dict:
    name = pair_dir.name
    manifest = tomllib.loads((pair_dir / "pair.toml").read_text())
    reps = manifest["acquisition"]["reps"]

    verifier = json.loads((pair_dir / "recover" / "fixtures" / "verifier.json").read_text())
    expect = verifier.get("sha256")   # only the sha256-preimage scheme uses it

    rec = load_module(pair_dir / "recover" / "recover.py")
    out = {"pair": name, "tier": manifest["pair"].get("tier"), "checks": {}}

    # Expectations come from the manifest, not from the arm's name. A negative
    # control is a pair on which recovery must fail on BOTH arms, and hardcoding
    # "vulnerable means it must verify" would make that pair inexpressible.
    oracle = manifest["oracle"]
    expected = {
        "vulnerable": oracle["expected_vulnerable"] == "recovered",
        "patched": oracle["expected_patched"] == "recovered",
    }
    scheme = verifier.get("scheme", "sha256-preimage")
    for arm, must_verify in expected.items():
        control = "ORC-1" if must_verify else "ORC-2"

        if scheme == "sha256-preimage":
            trace = pair_dir / "traces" / f"{arm}.bin.z"
            if not trace.exists():
                out["checks"][arm] = {"status": "MISSING", "trace": str(trace)}
                continue
            prefix, scores = rec.recover(rec.load(trace, reps))
            # The target's last byte carries no timing signal, so the side
            # channel supplies the prefix and the published verifier closes the
            # final eight bits over at most 256 candidates.
            verified = rec.finish(prefix, expect) is not None
            entry = {"min_separation_sigma": round(min(scores), 2),
                     "bytes_from_side_channel": len(prefix) - 1,
                     "bytes_brute_forced_against_verifier": 1}

        elif scheme == "ecdsa-pubkey-match":
            trace = pair_dir / "traces" / f"{arm}.csv.z"
            if not trace.exists():
                out["checks"][arm] = {"status": "MISSING", "trace": str(trace)}
                continue
            scalar = rec.recover_from(trace, verifier["curve"], verifier["hash"])
            # The recovery only reports success when its own guess reproduced the
            # public key (upstream's pubkey == d*G test), so a non-None result is
            # already a key verified under public material. It never sees the
            # private key.
            verified = scalar is not None
            entry = {"recovered_scalar_present": verified}

        else:
            out["checks"][arm] = {"status": "FAIL",
                                  "detail": f"unknown verifier scheme {scheme!r}"}
            continue

        ok = verified if must_verify else (not verified)
        entry.update({
            "control": control,
            "verified_under_published_key": verified,
            "expected_to_verify": must_verify,
            "status": "PASS" if ok else "FAIL",
        })
        out["checks"][arm] = entry
    out["status"] = ("PASS" if all(c.get("status") == "PASS"
                                   for c in out["checks"].values()) else "FAIL")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    pairs = sorted(p.parent for p in (REPO / "pairs").glob("*/pair.toml"))
    if a.pair:
        pairs = [p for p in pairs if p.name == a.pair]
    if not pairs:
        print("verify: no pairs found, so this is not a clean result", file=sys.stderr)
        return 2

    results = [verify_pair(p) for p in pairs]
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print(f"\n{r['pair']}  (tier {r['tier']})  -> {r['status']}")
            for arm, c in r["checks"].items():
                if c.get("status") == "MISSING":
                    print(f"  {arm:<11} MISSING trace")
                    continue
                verb = "verifies" if c["verified_under_published_key"] else "does not verify"
                want = "must verify" if c["expected_to_verify"] else "must NOT verify"
                extra = (f"   sep={c['min_separation_sigma']}sigma"
                         if "min_separation_sigma" in c else "")
                print(f"  {arm:<11} {c['control']}  recovered key {verb} "
                      f"({want})  -> {c['status']}{extra}")
    failed = [r for r in results if r["status"] != "PASS"]
    # Under --json, stdout must be only JSON. Appending a human summary to it
    # made the output unparsable for every caller, which is how the controls
    # reported that the oracle "produced no parsable result" while the oracle
    # itself was passing.
    summary = f"verify: {len(results) - len(failed)}/{len(results)} pair(s) verified"
    print(summary, file=sys.stderr if a.json else sys.stdout)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
