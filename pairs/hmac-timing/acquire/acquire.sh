#!/bin/sh
# Acquisition. PLATFORM-BOUND: needs the toolchain cell, the CPU, and the
# ability to pin to one core. Run rarely; its output is committed.
#
# It also destroys the key it generated. Everything that survives this script is
# either a timing or a digest.
set -eu
PAIR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$PAIR_DIR/../.." && pwd)"
CELL="${CELL:-localhost/ct-toolchain/gcc-bookworm:1}"
CPU="${CORPUS_CPU:-2}"
REPS="${CORPUS_REPS:-60}"
PAIR_ID="$(basename "$PAIR_DIR")"
OUT="$REPO/cache/build/$PAIR_ID/gcc-12.2.0-O2"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$OUT" "$PAIR_DIR/traces" "$PAIR_DIR/recover/fixtures"

for ARM in vulnerable patched; do
  podman run --rm --network=none \
    -v "$PAIR_DIR/src:/src:ro,Z" -v "$OUT:/out:rw,Z" \
    -e SOURCE_DATE_EPOCH=1700000000 "$CELL" /src/build.sh "$ARM" O2 /out
done

# Both arms are probed against the SAME key. The patched arm's traces exist so
# the oracle can require the recovery to FAIL on them; without that, a recovery
# that already knew the answer would be indistinguishable from one that works.
podman run --rm --network=none \
  -v "$OUT:/out:ro,Z" -v "$PAIR_DIR/traces:/traces:rw,Z" -v "$WORK:/work:rw,Z" \
  "$CELL" sh -c "
     set -e
     taskset -c $CPU /out/harness_vulnerable $REPS /traces/vulnerable.raw /work/secret.bin
     taskset -c $CPU /out/harness_patched    $REPS /traces/patched.raw    /work/secret2.bin
  "

python3 "$PAIR_DIR/acquire/finalise.py" \
    --pair "$PAIR_DIR" --secret "$WORK/secret.bin" --cpu "$CPU" --reps "$REPS"
echo "acquire: done. the key was destroyed with the temporary directory."
