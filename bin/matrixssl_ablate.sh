#!/usr/bin/env bash
# Build the mechanism-ablation variants of MatrixSSL 4.3.0 and acquire them.
#
# Five trees, each a copy of the verified 4-3-0 build under <work-dir>/build
# (bin/matrixssl_rebuild.sh), patched inside eccMulmodCt by
# bin/matrixssl_ablation.py --patch, rebuilt in the pinned gcc image, then timed
# by the site harness under every design bin/matrixssl_acquire.sh uses, with the
# same batches, measurements, core and repeats. Dumps land under
# <work-dir>/ablation/dumps and are brought into the repository by
# bin/matrixssl_ablation.py --import <work-dir>.
#
# Usage: matrixssl_ablate.sh <work-dir> [repeats]     (CORE=2 by default)
#        ACQUIRE=0 matrixssl_ablate.sh <work-dir>      builds only, no timing
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:?usage: matrixssl_ablate.sh <work-dir> [repeats]}"
# podman reads a relative bind source as a named volume, so resolve it.
WORK="$(cd "$WORK" && pwd)"
REPEATS="${2:-3}"
CORE="${CORE:-2}"
ACQUIRE="${ACQUIRE:-1}"
IMG=localhost/ct-toolchain/gcc-bookworm:1
SRC="$WORK/build/matrixssl-4-3-0-open"
B="$WORK/ablation/build"
OUT="$WORK/ablation/dumps"
[ -f "$SRC/crypto/libcrypt_s.a" ] || { echo "no built 4-3-0 tree at $SRC; run bin/matrixssl_rebuild.sh $WORK first" >&2; exit 1; }
mkdir -p "$B" "$OUT"
base_sha="$(sha256sum "$SRC/crypto/libcrypt_s.a" | cut -d' ' -f1)"
: > "$WORK/ablation/digests.txt"
for v in orig nop inplace evolvingoop evolving; do
  d="$B/mx-$v"
  if [ ! -f "$d/crypto/libcrypt_s.a" ]; then
    rm -rf "$d"; cp -a "$SRC" "$d"
    python3 "$REPO/bin/matrixssl_ablation.py" --patch "$v" \
      "$d/crypto/pubkey/ecc_math.c" "$d/crypto/pubkey/ecc_math.c"
    podman run --rm --network=none -v "$B:/w:Z" "$IMG" sh -c \
      "cd /w/mx-$v && make -C crypto >/dev/null 2>&1"
  fi
  n=$(podman run --rm --network=none -v "$B:/w:Z" "$IMG" sh -c \
        "nm -C /w/mx-$v/crypto/libcrypt_s.a | grep -c ' T eccMulmodCt' || true")
  [ "$n" = 1 ] || { echo "mx-$v: $n eccMulmodCt symbols, expected 1" >&2; exit 1; }
  sha="$(sha256sum "$d/crypto/libcrypt_s.a" | cut -d' ' -f1)"
  case "$v" in
    orig) [ "$sha" = "$base_sha" ] || { echo "mx-orig rebuilt to a different libcrypt_s.a than the verified tree" >&2; exit 1; } ;;
    *)    [ "$sha" != "$base_sha" ] || { echo "mx-$v is byte-identical to the shipped library; the patch did not take" >&2; exit 1; } ;;
  esac
  printf '%s  mx-%s/crypto/libcrypt_s.a\n' "$sha" "$v" >> "$WORK/ablation/digests.txt"
  printf '%s  mx-%s/crypto/pubkey/ecc_math.c\n' "$(sha256sum "$d/crypto/pubkey/ecc_math.c" | cut -d' ' -f1)" "$v" >> "$WORK/ablation/digests.txt"
  echo "  mx-$v built, libcrypt_s.a ${sha:0:12}"
done
[ "$ACQUIRE" = 1 ] || { echo "matrixssl_ablate: builds under $B (ACQUIRE=0)"; exit 0; }
for v in orig nop inplace evolvingoop evolving; do
  M="mx-$v"
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
echo "matrixssl_ablate: dumps under $OUT"
