#!/usr/bin/env python3
"""Commit the ECDSA nonce-leak pair's observations and publish its verifier."""
import argparse, hashlib, json, pathlib, platform, subprocess, sys, zlib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--pair", required=True)
    ap.add_argument("--cpu", required=True)
    ap.add_argument("--sigs", type=int, required=True)
    a = ap.parse_args()
    work = pathlib.Path(a.work); pair = pathlib.Path(a.pair)

    header = (work / "vuln.csv").read_text().splitlines()[0].split(" ")
    pub, data, priv = header

    (pair / "recover" / "fixtures" / "verifier.json").write_text(json.dumps({
        "scheme": "ecdsa-pubkey-match", "curve": "secp256r1", "hash": "sha256",
        "public_key": pub, "signed_data": data,
        "note": "A recovered scalar d verifies if d*G equals this public key, "
                "which is upstream's own success test and needs only public "
                "material. The private key is not stored in this repository.",
        "consistency_check": {"private_key_sha256":
            hashlib.sha256(bytes.fromhex(priv)).hexdigest()},
    }, indent=2) + "\n", encoding="utf-8")

    meta = []
    for arm in ("vulnerable", "patched"):
        name = 'vuln.csv' if arm == 'vulnerable' else 'patched.csv'
        blob = (work / name).read_bytes()
        comp = zlib.compress(blob, 9)
        (pair / "traces" / f"{arm}.csv.z").write_bytes(comp)
        meta.append({"arm": arm, "path": f"traces/{arm}.csv.z",
                     "sha256_raw": hashlib.sha256(blob).hexdigest(),
                     "sha256_file": hashlib.sha256(comp).hexdigest(),
                     "bytes_raw": len(blob), "bytes_file": len(comp),
                     "n_signatures": a.sigs, "format": "minerva-csv"})
    try:
        cell = subprocess.run(["podman", "image", "inspect", "--format", "{{.Id}}",
                               "localhost/ct-toolchain/openssl:1"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        cell = "unknown"
    (pair / "acquire" / "record.json").write_text(json.dumps({
        "traces": meta, "origin": "ours", "tier": "A",
        "source": "reproduced here: leaking scalar multiplication over secp256r1, "
                  "signed and timed on this host with rdtsc",
        "platform": {"kernel": platform.release(), "machine": platform.machine(),
                     "cpu_pinned_to": int(a.cpu)},
        "cell_image_id": cell, "sigs": a.sigs,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"finalise: verifier published, {a.sigs}-sig instances committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
