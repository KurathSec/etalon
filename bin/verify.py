#!/usr/bin/env python3
"""THE ORACLE. Runs every pair's recovery against its published verifier.

This is the deliverable a reader runs, and the constraint that shapes it is that
it must work from a cold clone with no analyser, no measurement and no hardware.
If it ever needs one of those, the acquisition and verification halves have leaked
into each other and the design has failed.

It is NOT stdlib-only, and saying so was wrong for five of the six recall-eligible
pairs. Each pair declares `[recovery] runtime`: `pure` runs on a stock interpreter,
`image` runs the recovery inside the pinned recovery container, because lattice
reduction needs fpylll and upstream's curve module is GPL and so is kept out of
this MIT tree. That is a real cost and the manifests carry it; regen counts the
split so the paper cannot restate the stdlib-only claim.

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
import subprocess
import sys
import tomllib

REPO = pathlib.Path(__file__).resolve().parent.parent


def load_module(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_RUNTIME_CACHE: dict[str, str | None] = {}


def runtime_unavailable(image: str) -> str | None:
    """Why an image-runtime recovery cannot run here, or None if it can.

    A recovery that needs the pinned image and finds no podman, or no image, must
    say so. Before this probe, a missing runtime surfaced as "recovered key does
    not verify": the subprocess failed, the wrapper returned None, and None meant
    "not recovered". That is the quiet failure INST-1 exists to catch, arriving
    through the oracle itself. Probed once per image and cached.
    """
    import shutil
    if image in _RUNTIME_CACHE:
        return _RUNTIME_CACHE[image]
    why = None
    if shutil.which("podman") is None:
        why = "podman is not installed"
    else:
        r = subprocess.run(["podman", "image", "exists", image],
                           capture_output=True, text=True)
        if r.returncode not in (0, 1):
            why = f"podman cannot run here (exit {r.returncode}): {r.stderr.strip()[:80]}"
        elif r.returncode == 1:
            why = (f"image {image} is not built; build it from its Containerfile "
                   f"under images/tools/ (podman build -t {image} images/tools/"
                   f"{image.split('/')[-1].split(':')[0]})")
    _RUNTIME_CACHE[image] = why
    return why


def verify_pair(pair_dir: pathlib.Path) -> dict:
    name = pair_dir.name
    manifest = tomllib.loads((pair_dir / "pair.toml").read_text())

    # A certified-negative control has no oracle: it is proven-constant-time code
    # scored for false positives, not a leak to recover, so there is nothing to verify.
    if manifest["pair"].get("role") == "certified-negative" or "oracle" not in manifest:
        return {"pair": name, "tier": manifest["pair"].get("tier"), "status": "NOT_RUN",
                "checks": {}, "reason": "no oracle: certified negative or non-recoverable control"}

    # A tier C pair has no reproduced oracle yet: its acquisition needs hardware
    # that is not in hand. It is reported as NOT_RUN, distinct from PASS and from
    # FAIL, so it neither claims a verification it cannot make nor counts as a
    # broken one.
    tier = manifest["pair"].get("tier")
    if tier == "C" or manifest["oracle"].get("predicate") == "not-yet-reproduced":
        return {"pair": name, "tier": tier, "status": "NOT_RUN",
                "checks": {}, "reason": "tier C: acquisition not reproduced here"}
    reps = manifest["acquisition"]["reps"]

    verifier = json.loads((pair_dir / "recover" / "fixtures" / "verifier.json").read_text())
    expect = verifier.get("sha256")   # only the sha256-preimage scheme uses it

    rec = load_module(pair_dir / "recover" / "recover.py")
    if manifest.get("recovery", {}).get("runtime") == "image":
        image = getattr(rec, "IMAGE", None)
        why = runtime_unavailable(image) if image else "recover.py names no IMAGE"
        if why:
            return {"pair": name, "tier": tier, "status": "NOT_RUN", "checks": {},
                    "runtime_unavailable": True,
                    "reason": f"recovery runtime unavailable: {why}"}
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
            if r["status"] == "NOT_RUN":
                print(f"  {r['reason']}")
                continue
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
    failed = [r for r in results if r["status"] == "FAIL"]
    verified = [r for r in results if r["status"] == "PASS"]
    not_run = [r for r in results if r["status"] == "NOT_RUN" and not r.get("runtime_unavailable")]
    # A pair whose recovery could not run is neither verified nor a tier-C not-run.
    # It is reported by name with the reason, and it fails the run, because an
    # oracle that did not run has established nothing.
    unavailable = [r for r in results if r.get("runtime_unavailable")]
    # Under --json, stdout must be only JSON. Appending a human summary to it
    # made the output unparsable for every caller, which is how the controls
    # reported that the oracle "produced no parsable result" while the oracle
    # itself was passing.
    summary = (f"verify: {len(verified)} verified, {len(failed)} failed, "
               f"{len(not_run)} not run (tier C)"
               + (f", {len(unavailable)} NOT RUN because the recovery runtime is "
                  f"unavailable ({unavailable[0]['reason']})" if unavailable else ""))
    print(summary, file=sys.stderr if a.json else sys.stdout)
    return 1 if (failed or unavailable) else 0


if __name__ == "__main__":
    sys.exit(main())
