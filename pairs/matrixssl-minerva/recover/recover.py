#!/usr/bin/env python3
"""Timing-ordered lattice attack on a MatrixSSL signing trace.

WHY THIS EXISTS
The paper grades the MatrixSSL fix at its site and reports the residual's
information content (AUC, selection purity), but until this script it made no
recovery ATTEMPT on the fixed build: the one lattice run in the record was
key-ordered, on the pre-fix trace, and shows information content rather than a
recovery. A reviewer asked for the experiment that is missing: order the
signatures by their timing, hand the fastest to the lattice, and report success
or failure at each budget as a bounded observation under (A, B, h).

WHAT IT RUNS
The vendored upstream Minerva attack (pairs/minerva/vendor/attack/attack.py,
MIT, pinned by commit) inside the pinned recovery image. That attack is already
timing-ordered but tolerates no misclassification: it sorts the signatures by elapsed time and
assigns each rank a leading-zero bound from the geometric profile. The trace
format is the one bin/matrixssl_trace.sh writes (header `<pubkey> <msg>`, rows
`r,s,cycles`), which is attack.py's own input format. The private key is
nowhere in the inputs; success is the attack printing a key that reproduces
the public key.

WHAT IT RECORDS
One JSON object per attempt: the trace, its digest, the budget (signatures the
lattice is given), the attack parameters, elapsed time, and the outcome. An
outcome of "not recovered" is a bounded observation at that budget, on this
host's trace, under this attack, and is reported as exactly that.

Usage: recover.py --trace <csv.z> [--budget N] [--timeout S] [--json]
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys, tempfile, time, zlib

HERE = pathlib.Path(__file__).resolve().parent
PAIR = HERE.parent
REPO = PAIR.parent.parent
IMAGE = "localhost/ct-toolchain/minerva-recover:1"
ATTACK = REPO / "pairs" / "minerva" / "vendor" / "attack"   # the vendored MIT attack, shared


def recover_from(trace: pathlib.Path, curve: str = "secp256r1", hash: str = "sha256",
                 budget: int | None = None, timeout: int = 7200,
                 params: dict | None = None) -> dict:
    """Run the timing-ordered attack; return a record, never raise on a miss."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="mx-recover-"))
    raw = zlib.decompress(trace.read_bytes())
    lines = raw.decode().splitlines()
    header, rows = lines[0], lines[1:]
    if budget is not None and budget < len(rows):
        # The attack sorts by time itself; the budget is how many signatures it is
        # GIVEN, taken in acquisition order so the selection is the attack's own.
        rows = rows[:budget]
    (work / "sigs.csv").write_text(header + "\n" + "\n".join(rows) + "\n")
    # Attack parameters: the vendored defaults unless overridden, and PASSED to the
    # attack with --params: attack.py carries its own defaults and ignores a
    # params.json it is not told about, which is how a first sweep ran the defaults
    # twice and reported two identical guess lists. In "full" mode the attack sorts
    # every signature by time and hands the fastest `dimension` to the lattice, so
    # the two knobs that matter are the pool (the budget) and `dimension`; the
    # `num` field only governs the "random" mode.
    p = json.loads((ATTACK / "params.json").read_text())
    if params:
        for k, v in params.items():
            if isinstance(v, dict) and isinstance(p.get(k), dict):
                p[k].update(v)
            else:
                p[k] = v
    p["attack"]["num"] = min(int(p["attack"]["num"]), len(rows))
    (work / "params.json").write_text(json.dumps(p, indent=1))
    t0 = time.time()
    try:
        r = subprocess.run(
            ["podman", "run", "--rm", "--network=none",
             "-v", f"{ATTACK}:/attack:ro,Z",
             "-v", f"{work}:/work:rw,Z", "-w", "/work",
             IMAGE, "sh", "-c",
             "cp /attack/attack.py /attack/__init__.py /work/ && cp /opt/ec.py /work/ "
             f"&& python3 attack.py --params /work/params.json {curve} {hash} /work/sigs.csv"],
            capture_output=True, text=True, timeout=timeout)
        out, err, rc, timed_out = r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as exc:
        out, err, rc, timed_out = (exc.stdout or "").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""), "", None, True
    finally:
        shutil.rmtree(work, ignore_errors=True)
    elapsed = time.time() - t0
    m = re.search(r"FOUND PRIVATE KEY \*\*\* : 0x([0-9a-f]+)", out)
    return {
        "trace": str(trace.relative_to(REPO)) if trace.is_relative_to(REPO) else str(trace),
        "trace_sha256": hashlib.sha256(trace.read_bytes()).hexdigest(),
        "signatures_in_trace": len(lines) - 1,
        "budget": len(rows),
        "attack": "pairs/minerva/vendor/attack/attack.py (timing-ordered, no error tolerance), "
                  "params: " + json.dumps({"dimension": p.get("dimension"), "betas": p.get("betas"),
                                           "attack": p.get("attack")}),
        "curve": curve, "hash": hash,
        "image": IMAGE,
        "elapsed_s": round(elapsed, 1),
        "timed_out": timed_out,
        "exit": rc,
        "outcome": "recovered" if m else ("timed out" if timed_out else "not recovered"),
        "scalar": m.group(1).zfill(64) if m else None,
        "stdout_tail": out[-1500:],
        "stderr_tail": err[-800:],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--budget", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--curve", default="secp256r1")
    ap.add_argument("--hash", default="sha256")
    ap.add_argument("--params", default=None, help="JSON overrides for params.json")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rec = recover_from(pathlib.Path(a.trace), curve=a.curve, hash=a.hash,
                       budget=a.budget, timeout=a.timeout,
                       params=json.loads(a.params) if a.params else None)
    if a.json:
        print(json.dumps(rec, indent=1))
    else:
        print(f"{rec['outcome']} at budget {rec['budget']} in {rec['elapsed_s']}s"
              + (f": {rec['scalar'][:16]}..." if rec["scalar"] else ""))
    return 0 if rec["outcome"] == "recovered" else 1


if __name__ == "__main__":
    sys.exit(main())
