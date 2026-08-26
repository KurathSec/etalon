#!/usr/bin/env python3
"""Measure the recovery's success rate over random signature subsets, and its wall
time, for the recovery cards (W7). The vendored lattice attack supports type=random
with a seed; we vary the seed at a few subset sizes and record how often the key
verifies under the published key and how long it takes. Emits
results/recovery_robustness.json.

    bin/recovery_robustness.py [--pair ecdsa-nonce] [--seeds 10]
"""
from __future__ import annotations
import argparse, json, pathlib, re, subprocess, sys, tempfile, time, zlib

REPO = pathlib.Path(__file__).resolve().parent.parent
IMAGE = "localhost/ct-toolchain/minerva-recover:1"


def run_once(pair_dir, trace, curve, hash_, num, seed, base_params):
    work = pathlib.Path(tempfile.mkdtemp(prefix="rob-"))
    (work / "sigs.csv").write_bytes(zlib.decompress(trace.read_bytes()))
    p = dict(base_params)
    p["attack"] = dict(base_params["attack"])
    p["attack"].update({"type": "random", "num": num, "seed": seed})
    (work / "params.json").write_text(json.dumps(p))
    t0 = time.time()
    try:
        r = subprocess.run(
            ["podman", "run", "--rm", "--network=none",
             "-v", f"{pair_dir}/vendor/attack:/attack:ro,Z",
             "-v", f"{work}:/work:rw,Z", "-w", "/work", IMAGE, "sh", "-c",
             "cp /attack/attack.py /attack/__init__.py /work/ && cp /opt/ec.py /work/ "
             f"&& python3 attack.py {curve} {hash_} /work/sigs.csv --params /work/params.json"],
            capture_output=True, text=True, timeout=600)
        ok = bool(re.search(r"FOUND PRIVATE KEY", r.stdout))
    except subprocess.TimeoutExpired:
        ok = False
    finally:
        import shutil; shutil.rmtree(work, ignore_errors=True)
    return ok, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", default="ecdsa-nonce")
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--nums", default="3200,4000,5000")
    a = ap.parse_args()
    pair_dir = REPO / "pairs" / a.pair
    man = __import__("tomllib").loads((pair_dir / "pair.toml").read_text())
    ver = json.loads((pair_dir / man["oracle"]["verifier"]).read_text())
    trace = pair_dir / "traces" / "vulnerable.csv.z"
    base_params = json.loads((pair_dir / "vendor" / "attack" / "params.json").read_text())

    results = []
    for num in [int(x) for x in a.nums.split(",")]:
        succ, times = 0, []
        for s in range(a.seeds):
            ok, dt = run_once(pair_dir, trace, ver["curve"], ver["hash"], num, 1000 + s, base_params)
            succ += ok; times.append(dt)
            print(f"  num={num} seed={1000+s}: {'OK' if ok else 'fail'} {dt:.2f}s", flush=True)
        times.sort()
        results.append({"num_signatures": num, "seeds": a.seeds, "recovered": succ,
                        "success_rate": f"{succ}/{a.seeds}",
                        "median_wall_s": round(times[len(times)//2], 2)})
    doc = {"finding": "recovery-robustness", "pair": a.pair,
           "note": "success of the vendored lattice attack over random signature subsets "
                   "of the committed observations, seed varied; a probabilistic attack, so "
                   "the rate is a real measurement, not trivially one.",
           "results": results}
    # One file per pair. A fixed output path meant sweeping a second pair silently
    # overwrote the first pair's curve, which is how a committed result disappears.
    name = ("recovery_robustness.json" if a.pair == "ecdsa-nonce"
            else f"recovery_robustness_{a.pair}.json")
    (REPO / "results" / name).write_text(json.dumps(doc, indent=2) + "\n")
    print("wrote results/" + name)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    sys.exit(main())
