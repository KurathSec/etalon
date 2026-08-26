#!/bin/sh
# Acquire the MatrixSSL nonce-bit-length residual, with repeats, keeping every dump.
#
# What this changes from the original acquisition. That one took ONE acquisition per
# design, so every interval the paper reports on this case bounds sampling within a
# single run and nothing bounds the spread between runs; the paper had to say so, in
# the abstract. This takes REPEATS, from the same retained build, so the between-run
# spread is measured rather than conceded.
#
# It also runs all four designs. The harness that produced the samedigit and diffdigit
# dumps was never committed, so two of the four could not be reproduced from anything
# the repository held.
#
# Usage: matrixssl_acquire.sh <work-dir-from-matrixssl_rebuild> [repeats]
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:?usage: matrixssl_acquire.sh <work-dir> [repeats]}"
REPEATS="${2:-3}"
CORE="${CORE:-2}"
B="$WORK/build"
OUT="$WORK/dumps"
mkdir -p "$OUT"
[ -d "$B" ] || { echo "no build tree at $B; run bin/matrixssl_rebuild.sh first" >&2; exit 1; }

for v in 4-2-1 4-3-0 4-6-0; do
  M="matrixssl-$v-open"
  # Build the harness once per version, against the retained libraries.
  podman run --rm --network=none -v "$B:/w:Z" \
    -v "$REPO/pairs/matrixssl-minerva/harness:/h:ro,Z" \
    -v "$REPO/src/corpus/score/adapters:/driver:ro,Z" \
    -v "$OUT:/out:Z" localhost/ct-toolchain/dudect:1 sh -c \
    "cd /w && gcc -O2 -I/driver -I$M -I$M/crypto -I$M/core/include -I$M/core/osdep/include \
       -I$M/core -o /out/harness-$v /h/dudect_mx.c $M/crypto/libcrypt_s.a $M/core/libcore_s.a -lm"
  for design in same bit255 samedigit diffdigit; do
    r=1
    while [ "$r" -le "$REPEATS" ]; do
      tag="$v.$design.r$r"
      if [ -f "$OUT/$tag.bin" ]; then r=$((r+1)); continue; fi
      podman run --rm --network=none -v "$B:/w:Z" -v "$OUT:/out:Z" \
        localhost/ct-toolchain/dudect:1 sh -c \
        "cd /w && CONTROL=$design DUDECT_BATCHES=3 DUDECT_MEASUREMENTS=20000 \
           DUDECT_RAW_DUMP=/out/$tag.bin taskset -c $CORE /out/harness-$v 2>&1 \
         | grep -E 'max t|VERDICT' | tail -2" | sed "s/^/  $tag  /"
      r=$((r+1))
    done
  done
done
echo "matrixssl_acquire: dumps under $OUT"
