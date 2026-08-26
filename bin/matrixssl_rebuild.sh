#!/bin/sh
# Rebuild the three MatrixSSL trees and KEEP them.
#
# The original acquisition script built into a `mktemp -d` and ran `rm -rf` on it at
# exit. That is why nothing about this case could be re-run: the binaries the numbers
# were taken on did not survive the run that produced them, and the paper had to say so.
# This script keeps the tree, records a digest for every library it builds, and leaves
# the harnesses in place so an acquisition can be repeated without a rebuild.
#
# Sources are the archived github.com/BlobbyBob/matrixssl mirror at tags <ver>-open,
# verified against the sha256 pinned in pairs/matrixssl-minerva/acquire/acquire.sh.
# A mismatch is fatal: a rebuild that silently takes different source than the one the
# committed numbers were measured on is worse than no rebuild.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:?usage: matrixssl_rebuild.sh <work-dir>}"
IMG=localhost/ct-toolchain/gcc-bookworm:1
mkdir -p "$WORK/src" "$WORK/build"

sha_4_2_1=3bbddd70f54ba6c8ec3730cb666af2b7abf617f7468410db094f31b21cd924d2
sha_4_3_0=b6fe9a3c6290ef10169ebf35d65bc7e1ac54ce8f360c6f71bd0630de68c83667
sha_4_6_0=87be70df27356fec1221011b8ac6f12a4ad1e7e7eaaaf73d73bc94ad9be02dd9

for v in 4-2-1 4-3-0 4-6-0; do
  key="sha_$(echo "$v" | tr - _)"
  want="$(eval echo \$$key)"
  tgz="$WORK/src/$v-open.tar.gz"
  if [ ! -f "$tgz" ]; then
    curl -sSL --max-time 180 -o "$tgz" \
      "https://github.com/BlobbyBob/matrixssl/archive/refs/tags/$v-open.tar.gz"
  fi
  got="$(sha256sum "$tgz" | cut -d' ' -f1)"
  if [ "$got" != "$want" ]; then
    echo "matrixssl_rebuild: $v sha256 $got != pinned $want" >&2; exit 1
  fi
  echo "  $v sha256 verified"

  d="$WORK/build/matrixssl-$v-open"
  if [ ! -f "$d/crypto/libcrypt_s.a" ]; then
    tar -C "$WORK/build" -xzf "$tgz"
    cp "$d/configs/default/cryptoConfig.h"    "$d/crypto/"
    cp "$d/configs/default/coreConfig.h"      "$d/core/"
    cp "$d/configs/default/matrixsslConfig.h" "$d/matrixssl/"
    podman run --rm --network=none -v "$WORK/build:/w:Z" "$IMG" sh -c \
      "cd /w/matrixssl-$v-open && make -C core >/dev/null 2>&1 && make -C crypto >/dev/null 2>&1"
  fi
  # eccMulmodCt is the constant-time routine added in 4.3.0. Its presence is the
  # difference between the pre-fix arm and the two fixed ones, so it is asserted
  # rather than assumed: a build that silently lost it would read as a clean fix.
  n=$(podman run --rm --network=none -v "$WORK/build:/w:Z" "$IMG" sh -c \
        "nm -C /w/matrixssl-$v-open/crypto/libcrypt_s.a | grep -c ' T eccMulmodCt' || true")
  case "$v:$n" in
    4-2-1:0) ;;                      # absent before the fix, as it must be
    4-3-0:1|4-6-0:1) ;;              # present after it
    *) echo "matrixssl_rebuild: $v has $n eccMulmodCt symbols, expected 0 (4-2-1) or 1" >&2
       exit 1 ;;
  esac
  echo "  $v built, eccMulmodCt symbols: $n"
done

# Digest every library actually built, so an acquisition can name the binary it ran on.
: > "$WORK/build-digests.txt"
for v in 4-2-1 4-3-0 4-6-0; do
  for lib in crypto/libcrypt_s.a core/libcore_s.a; do
    printf '%s  matrixssl-%s-open/%s\n' \
      "$(sha256sum "$WORK/build/matrixssl-$v-open/$lib" | cut -d' ' -f1)" "$v" "$lib"
  done
done >> "$WORK/build-digests.txt"
echo "matrixssl_rebuild: three trees built and RETAINED under $WORK/build"
echo "matrixssl_rebuild: digests in $WORK/build-digests.txt"
