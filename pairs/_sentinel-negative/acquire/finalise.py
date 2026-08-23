#!/usr/bin/env python3
"""Publish the verifier, compress the traces, and record what was measured.

Splits cleanly from the portable half: this runs once on the acquisition
platform, and everything it writes is committed. The key it reads is deleted by
its caller immediately afterwards.
"""
import argparse, hashlib, json, pathlib, platform, subprocess, sys, zlib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--secret", required=True)
    ap.add_argument("--cpu", required=True)
    ap.add_argument("--reps", required=True, type=int)
    a = ap.parse_args()
    pair = pathlib.Path(a.pair)

    secret = pathlib.Path(a.secret).read_bytes()
    if len(secret) != 16:
        print("finalise: secret is not 16 bytes", file=sys.stderr)
        return 2

    # The published verifier. This is the analogue of a public key: it certifies
    # a candidate without revealing the answer.
    digest = hashlib.sha256(secret).hexdigest()
    (pair / "recover" / "fixtures" / "verifier.json").write_text(
        json.dumps({
            "scheme": "sha256-preimage",
            "note": "A recovered candidate verifies if its SHA-256 equals this digest. "
                    "The digest reveals nothing about the key, so the committed traces "
                    "are the only channel that carries it.",
            "tag_len": 16,
            "sha256": digest,
        }, indent=2) + "\n", encoding="utf-8")

    # Compress the traces and record both digests. sha256_raw is the contract;
    # sha256_file may legitimately change if the compressor does.
    meta = []
    for arm in ("vulnerable", "patched"):
        raw = pair / "traces" / f"{arm}.raw"
        blob = raw.read_bytes()
        comp = zlib.compress(blob, 9)
        out = pair / "traces" / f"{arm}.bin.z"
        out.write_bytes(comp)
        raw.unlink()
        meta.append({
            "arm": arm, "path": f"traces/{arm}.bin.z",
            "sha256_raw": hashlib.sha256(blob).hexdigest(),
            "sha256_file": hashlib.sha256(comp).hexdigest(),
            "bytes_raw": len(blob), "bytes_file": len(comp),
            "shape": [16, 256, a.reps], "dtype": "u32le", "unit": "cycles",
        })

    try:
        cell = subprocess.run(
            ["podman", "image", "inspect", "--format", "{{.Id}}",
             "localhost/ct-toolchain/gcc-bookworm:1"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        cell = "unknown"

    (pair / "acquire" / "record.json").write_text(json.dumps({
        "traces": meta,
        "platform": {
            "kernel": platform.release(), "machine": platform.machine(),
            "cpu_pinned_to": int(a.cpu),
            "note": "This host has three core frequency tiers and turbo cannot be "
                    "disabled without root, so measurements are pinned to one "
                    "performance core. The pair is synthetic and its signal is "
                    "amplified far above the noise floor, so this is sufficient "
                    "here and would not be for a real pair.",
        },
        "cell_image_id": cell,
        "reps": a.reps,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"finalise: verifier published, {len(meta)} traces compressed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
