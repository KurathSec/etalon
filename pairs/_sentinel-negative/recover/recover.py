#!/usr/bin/env python3
"""Recover the tag from recorded timings. PORTABLE: stdlib only, no hardware.

This is the half of the oracle that a reader runs. It never sees the key, the
queries, or the source of the arm it is attacking. It sees an array of cycle
counts and nothing else.

The attack is the textbook one against an early-exit comparison. A probe whose
first k bytes are correct and whose byte k is wrong costs k+1 units of work; if
byte k is also correct it costs k+2. So for each position, the guess with the
largest central timing is the true byte. Medians rather than means, because a
scheduler interruption produces an enormous outlier and a mean would follow it.

THE LAST BYTE HAS NO SIGNAL, and this is a property of the target rather than a
limitation of the analysis. At the final position a correct guess and a wrong
one both execute all TAG_LEN comparisons: the wrong one returns from inside the
loop, the correct one falls out of it, and the work done is identical. So the
side channel yields TAG_LEN - 1 bytes and the remaining eight bits are closed by
testing at most 256 candidates against the published verifier, which is what a
real attacker does because the verifier is public and the test is free.

That does not make the oracle circular. The verifier answers yes or no on a
complete candidate, so on its own it is a 2^128 search; the timings are what
reduce that to 2^8. Run the same recovery against the patched arm and the first
fifteen bytes are noise, so the brute force ranges over 256 candidates out of
2^128 and fails, which is exactly what control ORC-2 requires it to do.
"""
from __future__ import annotations

import argparse
import pathlib
import statistics
import struct
import sys
import zlib

TAG_LEN = 16
N_GUESS = 256


def load(path: pathlib.Path, reps: int) -> list[list[list[int]]]:
    blob = path.read_bytes()
    if path.suffix == ".z":
        blob = zlib.decompress(blob)
    n = len(blob) // 4
    flat = struct.unpack(f"<{n}I", blob[: n * 4])
    want = TAG_LEN * N_GUESS * reps
    if n != want:
        raise SystemExit(f"recover: expected {want} samples, found {n}")
    out = []
    i = 0
    for _ in range(TAG_LEN):
        row = []
        for _ in range(N_GUESS):
            row.append(list(flat[i:i + reps]))
            i += reps
        out.append(row)
    return out


def recover(trace) -> tuple[bytes, list[float]]:
    """Return the recovered tag and a per-position separation score.

    The score is how far the winner stands above the rest, in units of the
    spread of the losers. It is reported rather than thresholded: a caller that
    wants to know whether recovery was decisive can look, and a caller that
    only wants the answer can ignore it. What it must never do is decide
    success, because success is decided by the published verifier alone.
    """
    tag, scores = bytearray(), []
    for k in range(TAG_LEN):
        med = [statistics.median(trace[k][g]) for g in range(N_GUESS)]
        best = max(range(N_GUESS), key=lambda g: med[g])
        others = [med[g] for g in range(N_GUESS) if g != best]
        spread = statistics.pstdev(others) or 1.0
        scores.append((med[best] - statistics.median(others)) / spread)
        tag.append(best)
    return bytes(tag), scores


def finish(prefix: bytes, sha256_hex: str) -> bytes | None:
    """Close the final byte against the published verifier.

    Returns the complete key, or None when no candidate verifies. Returning None
    rather than a best guess matters: the caller must be able to distinguish
    "recovered" from "did not recover", and a function that always returns
    something forces the caller to invent that distinction itself.
    """
    import hashlib
    for last in range(N_GUESS):
        cand = prefix[:TAG_LEN - 1] + bytes([last])
        if hashlib.sha256(cand).hexdigest() == sha256_hex:
            return cand
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--verifier", help="verifier.json, to close the final byte")
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    tag, scores = recover(load(pathlib.Path(a.trace), a.reps))
    if a.verifier:
        import json
        digest = json.loads(pathlib.Path(a.verifier).read_text())["sha256"]
        full = finish(tag, digest)
        if full is None:
            print("no candidate verified under the published key")
            return 1
        tag = full
    if not a.quiet:
        print(f"recovered: {tag.hex()}")
        print(f"separation per position (winner above the field, in sigmas):")
        print("  " + " ".join(f"{s:5.1f}" for s in scores))
    else:
        print(tag.hex())
    return 0


if __name__ == "__main__":
    sys.exit(main())
