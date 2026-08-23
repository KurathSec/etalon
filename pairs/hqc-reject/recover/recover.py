#!/usr/bin/env python3
"""Recover the secret key from rejection-sampling timings. Portable, stdlib only.

For each key position the mean draw count is 256/threshold, and each draw costs a
roughly fixed number of cycles, so the mean cycle count is proportional to
256/threshold. Calibrating the per-draw cost from the data, the threshold (the
secret byte, up to the |1) is recovered directly. A direct-recovery timing
attack: no lattice, the secret falls straight out of the mean timings.
"""
from __future__ import annotations
import argparse, pathlib, statistics, struct, zlib, hashlib

KEY_LEN = 8

def load(path, trials):
    blob = path.read_bytes()
    if path.suffix == ".z": blob = zlib.decompress(blob)
    flat = struct.unpack(f"<{len(blob)//4}I", blob)
    return [list(flat[p*trials:(p+1)*trials]) for p in range(KEY_LEN)]

def load_cal(path):
    # calibration: list of (threshold, mean_cycles), public
    rows = [l.split() for l in pathlib.Path(path).read_text().splitlines() if l.strip()]
    return [(int(r[0]), float(r[1])) for r in rows]

def thr_from_mean(m, cal):
    # nearest-calibration-point inversion, then refine to the closest threshold
    best = min(cal, key=lambda tc: abs(tc[1] - m))
    return best[0]

def recover_cal(trace, cal):
    # Use the MEAN, matching the calibration statistic. Clip only extreme timing
    # spikes (top 1%, scheduler interrupts), NOT the geometric draw-count tail,
    # because the mean of that tail is exactly the leak signal.
    out = []
    for col in trace:
        s = sorted(col); keep = s[:int(len(s)*0.99)]
        m = sum(keep) / len(keep)
        out.append(thr_from_mean(m, cal))
    return bytes((t & 0xff) for t in out)

def recover(trace):
    # mean cycles per position ~ base + per_draw * (256/thr). Calibrate base and
    # per_draw from the spread across positions, then invert for each threshold.
    means = [statistics.median(sorted(col)[:int(len(col)*0.9)]) for col in trace]  # trim tail
    # draws_pos = 256/thr; cycles = base + k*draws. We do not know base,k a priori,
    # so fit: the position with the largest mean has the smallest thr. Use a
    # two-point calibration is unstable; instead brute-force (base,k) to best map
    # each mean to an integer threshold in [1,255] and pick the consistent one.
    best = None
    for k in range(20, 400, 2):
        for base in range(0, 4000, 50):
            cand = []
            ok = True
            for m in means:
                draws = (m - base) / k
                if draws < 1: ok = False; break
                thr = round(256 / draws)
                if thr < 1 or thr > 255: ok = False; break
                cand.append(thr)
            if ok:
                # score: how integer-consistent the mapping is
                err = sum(abs((base + k*256.0/t) - m) for t,m in zip(cand,means))
                if best is None or err < best[0]: best = (err, cand)
    return bytes((t & 0xff) for t in best[1]) if best else None

def finish(prefix, sha):
    # the |1 in the sampler means recovered thr has its low bit forced; the true
    # secret byte's low bit is unknown, so brute-force the KEY_LEN low bits.
    for mask in range(1 << KEY_LEN):
        cand = bytes(((prefix[i] & 0xfe) | ((mask >> i) & 1)) for i in range(KEY_LEN))
        if hashlib.sha256(cand).hexdigest() == sha: return cand
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True); ap.add_argument("--trials", type=int, default=20000)
    ap.add_argument("--verifier")
    a = ap.parse_args()
    pref = recover(load(pathlib.Path(a.trace), a.trials))
    if pref is None: print("no recovery"); return 1
    if a.verifier:
        import json
        sha = json.loads(pathlib.Path(a.verifier).read_text())["sha256"]
        full = finish(pref, sha)
        if full is None: print("no candidate verified"); return 1
        print(f"recovered: {full.hex()}"); return 0
    print(f"recovered(prefix): {pref.hex()}"); return 0

if __name__ == "__main__": raise SystemExit(main())
