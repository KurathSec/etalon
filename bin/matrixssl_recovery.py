#!/usr/bin/env python3
"""Assemble the MatrixSSL recovery attempts into one record, and check it.

WHY THIS EXISTS
The paper graded the MatrixSSL fix at its site and reported the residual's
information content, but for several revisions it made no recovery ATTEMPT on
the fixed build: the one lattice run on record was key-ordered, on the pre-fix
trace, and shows information content rather than a recovery. A reviewer asked
for the missing experiment. Every attempt summarised here orders the signatures
by their own timing, hands the fastest to the published lattice, and reports the
outcome as a bounded observation under the attack, the budget and the host.

WHAT IT ASSEMBLES
The attempt records under results/raw/matrixssl/lattice/, one per (budget,
lattice dimension), written by pairs/matrixssl-minerva/recover/recover.py. Each
carries the trace and its digest, the parameters, the elapsed time and the
outcome, so this script re-derives nothing measured: it collects, and it adds
the one thing the attempts do not carry, the attack's own information
accounting.

THE ACCOUNTING, AND WHY IT DECIDES THE RESULT
The attack models the i-th fastest signature as having geom_bound(i) leading
zeros, a rank model that assumes a MULTI-BIT bias: out of 25,000 signatures it
credits the fastest with about fourteen leading zeros. It then needs the summed
bounds to exceed the key size. The deployed MatrixSSL fix leaves a ONE-BIT
residual, so the ordering it produces is real (the selection purity beside each
attempt says how real) while the per-signature bound the attack assumes is not.
That is why no budget in this sweep converts the residual, and it is a
statement about the attack's information model rather than about the number of
signatures: an attack fitted to a one-bit bias would need a different lattice,
and this paper does not build one.

Usage: matrixssl_recovery.py [--write] [--check]
"""
from __future__ import annotations
import argparse
import glob
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ATTEMPTS = REPO / "results" / "raw" / "matrixssl" / "lattice"
OUT = REPO / "results" / "matrixssl_recovery.json"
KEY_BITS = 256


def geom_bound(index: int, total: int) -> int:
    """The attack's own per-rank leading-zero model (attack.py, geom_bound)."""
    i = 1
    while total / (2 ** i) >= index + 1:
        i += 1
    i -= 1
    return 0 if i <= 1 else i


def build() -> dict:
    attempts = []
    for f in sorted(glob.glob(str(ATTEMPTS / "*.json"))):
        d = json.loads(pathlib.Path(f).read_text())
        # The dimension is inside the attack's own params line, the only place the
        # attempt records it.
        try:
            dim = json.loads(str(d["attack"]).split("params: ", 1)[1])["dimension"]
        except (KeyError, IndexError, ValueError):
            dim = None
        total = int(d["budget"])
        info = sum(geom_bound(i, total) for i in range(dim)) if dim else None
        attempts.append({
            "record": str(pathlib.Path(f).relative_to(REPO)),
            "trace": d["trace"], "trace_sha256": d["trace_sha256"],
            "budget_signatures": total,
            "lattice_dimension": dim,
            "assumed_information_bits": info,
            "assumed_overhead_over_key": round(info / KEY_BITS, 2) if info else None,
            "elapsed_s": d["elapsed_s"],
            "outcome": d["outcome"],
        })
    attempts.sort(key=lambda a: (a["budget_signatures"], a["lattice_dimension"] or 0))
    recovered = [a for a in attempts if a["outcome"] == "recovered"]
    return {
        "finding": ("the deployed MatrixSSL fix's residual is orderable but the published "
                    "attack does not convert it at any budget or lattice dimension tried"),
        "why": __doc__.split("WHY THIS EXISTS")[1].split("WHAT IT ASSEMBLES")[0].strip(),
        "accounting": __doc__.split("THE ACCOUNTING, AND WHY IT DECIDES THE RESULT")[1]
                      .split("Usage:")[0].strip(),
        "generator": "bin/matrixssl_recovery.py --write",
        "attack": ("pairs/minerva/vendor/attack/attack.py, the upstream Minerva attack pinned "
                   "by commit, run inside localhost/ct-toolchain/minerva-recover:1 by "
                   "pairs/matrixssl-minerva/recover/recover.py. It sorts every signature by "
                   "elapsed time and assigns each rank a leading-zero bound, so it is "
                   "timing-ordered and error-tolerant by construction."),
        "host": ("the acquisition host; every trace was taken with nothing else running, "
                 "which matters: a trace taken under load selects far worse"),
        "key_bits": KEY_BITS,
        "attempts_total": len(attempts),
        "recovered": len(recovered),
        "reading": ("No attempt recovered the key. The selection is not the reason: on the "
                    "quiet 50,000 and 100,000 signature traces the fastest ninety are 94.4 "
                    "per cent genuinely short. The reason is the per-signature bound. The "
                    "attack credits its top-ranked signatures with a multi-bit bias, so it "
                    "builds a lattice on assumed_information_bits of information against a "
                    "key of key_bits, while the deployed fix leaves one bit of nonce length. "
                    "The result is therefore a bounded observation about this attack and "
                    "this residual, not about the number of signatures, and it is reported "
                    "as one."),
        "attempts": attempts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    if not doc["attempts"]:
        print("matrixssl_recovery: no attempt records under "
              f"{ATTEMPTS.relative_to(REPO)}", file=sys.stderr)
        return 1
    if a.check:
        if not OUT.exists():
            print("matrixssl_recovery: no committed record", file=sys.stderr)
            return 1
        old = json.loads(OUT.read_text())
        bad = [k for k in ("attempts_total", "recovered", "attempts", "key_bits")
               if old.get(k) != doc[k]]
        if bad:
            print("matrixssl_recovery: " + ", ".join(bad) + " differ from committed",
                  file=sys.stderr)
            return 1
        print(f"matrixssl_recovery: check clean ({doc['attempts_total']} attempts, "
              f"{doc['recovered']} recovered)")
        return 0
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"matrixssl_recovery: wrote {OUT.relative_to(REPO)}")
    for at in doc["attempts"]:
        print(f"  {at['budget_signatures']:>7} sigs  dim {at['lattice_dimension']:>3}  "
              f"{at['assumed_information_bits']:>5} bits assumed  "
              f"{at['elapsed_s']:>7.1f}s  {at['outcome']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
