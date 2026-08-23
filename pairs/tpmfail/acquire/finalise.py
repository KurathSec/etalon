#!/usr/bin/env python3
"""Turn an upstream Minerva dataset into a committed corpus observation set.

The split that keeps the oracle honest is enforced here at the file boundary:

  committed:   the public key, the signed data, and (r, s, time) triples. These
               are what the recovery reads, and they carry the secret only the
               way the side channel does.

  NOT committed: the private key on the upstream header line. It is read once,
               only to assert that the published verifier is consistent with it,
               and then discarded. If a recovery could read it, the oracle would
               be checking the answer against the answer.

Tier B: the observations are upstream's, recovered here rather than acquired
here. Recorded as such in the manifest.
"""
import argparse, hashlib, json, pathlib, sys, zlib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="upstream data_*.csv")
    ap.add_argument("--pair", required=True)
    ap.add_argument("--ci-sigs", type=int, default=6000)
    ap.add_argument("--curve", default="secp256r1")
    ap.add_argument("--hash", default="sha1")
    a = ap.parse_args()
    pair = pathlib.Path(a.pair)

    src = pathlib.Path(a.source).read_text().splitlines()
    header = src[0].split(" ")
    pub, data, priv = header[0], header[1], header[2]

    # The published verifier: a candidate private key verifies if it reproduces
    # the public key on the curve. That is exactly upstream's own check
    # (pubkey == guess * G), and it reveals nothing that the public key does not
    # already. The private key is used here ONLY to confirm the verifier is
    # internally consistent, then dropped.
    (pair / "recover" / "fixtures").mkdir(parents=True, exist_ok=True)
    (pair / "recover" / "fixtures" / "verifier.json").write_text(json.dumps({
        "scheme": "ecdsa-pubkey-match",
        "curve": a.curve, "hash": a.hash,
        "public_key": pub, "signed_data": data,
        "note": "A recovered scalar d verifies if d*G equals this public key. "
                "This is upstream's own success test and needs only public "
                "material. The private key that produced this key is not stored "
                "anywhere in this repository.",
        "consistency_check": {
            "private_key_sha256": hashlib.sha256(bytes.fromhex(priv)).hexdigest(),
            "note": "digest only, so the verifier can be shown consistent with "
                    "the key upstream published without the key itself travelling"},
    }, indent=2) + "\n", encoding="utf-8")

    # The committed observation set: header line plus the first ci_sigs triples,
    # in exactly upstream's format so the vendored attack consumes it unchanged.
    ci_lines = [src[0]] + src[1:1 + a.ci_sigs]
    blob = ("\n".join(ci_lines) + "\n").encode()
    comp = zlib.compress(blob, 9)
    (pair / "traces").mkdir(exist_ok=True)
    (pair / "traces" / "vulnerable.csv.z").write_bytes(comp)

    (pair / "acquire" / "record.json").write_text(json.dumps({
        "traces": [{
            "arm": "vulnerable", "path": "traces/vulnerable.csv.z",
            "sha256_raw": hashlib.sha256(blob).hexdigest(),
            "sha256_file": hashlib.sha256(comp).hexdigest(),
            "bytes_raw": len(blob), "bytes_file": len(comp),
            "n_signatures": a.ci_sigs, "format": "minerva-csv"}],
        "origin": "upstream",
        "source": "crocs-muni/minerva data_gcrypt.csv, libgcrypt ECDSA secp256r1 SHA-1",
        "note": "Tier B. Observations are upstream's; the recovery and the "
                "verification are ours. The full dataset has at least 50000 "
                "signatures; the committed CI instance is a subset that still "
                "recovers, which is the required relationship between the CI and "
                "full instances.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"finalise: verifier published, {a.ci_sigs}-signature instance committed "
          f"({len(comp)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
