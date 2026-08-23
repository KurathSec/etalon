#!/bin/sh
# Tier-A acquisition: build the arms in the OpenSSL cell, sign+time here, commit.
set -eu
PAIR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$PAIR_DIR/../.." && pwd)"
CELL="${CELL:-localhost/ct-toolchain/openssl:1}"
CPU="${CORPUS_CPU:-2}"
N="${CORPUS_SIGS:-6000}"
OUT="$REPO/cache/build/ecdsa-nonce/gcc-O2"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT" "$PAIR_DIR/traces" "$PAIR_DIR/recover/fixtures"
for ARM in vulnerable patched; do
  podman run --rm --network=none -v "$PAIR_DIR/src:/src:ro,Z" -v "$OUT:/out:rw,Z" \
    -e SOURCE_DATE_EPOCH=1700000000 "$CELL" /src/build.sh "$ARM" O2 /out
done
# The vulnerable and patched arms use the SAME key, so the oracle can require the
# recovery to fail on the patched arm's timings.
podman run --rm --network=none -v "$OUT:/out:ro,Z" -v "$WORK:/w:rw,Z" "$CELL" sh -c "
  set -e
  taskset -c $CPU /out/harness_vulnerable $N /w/vuln.csv
  # patched arm: same code path, its timing does not leak bitlength
  taskset -c $CPU /out/harness_patched   $N /w/patched.csv
"
python3 "$PAIR_DIR/acquire/finalise.py" --work "$WORK" --pair "$PAIR_DIR" --cpu "$CPU" --sigs "$N"
echo "acquire: done"
