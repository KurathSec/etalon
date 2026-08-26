#!/usr/bin/env bash
# Acquisition for matrixssl-minerva. Builds three MatrixSSL versions and measures the
# nonce-bit-length residual on the ECC scalar multiplication. This is the headline
# fix-verification case: MatrixSSL added a constant-time eccMulmod in 4.3.0 "in
# response to the Minerva attack" (release notes), enabled by default, that balances the
# leading-zero phase by operation count but not by cost, so the fix attenuates the leak
# about fivefold without removing it and the residual persists through the latest open
# release. NOTE: an earlier revision of this script blamed the loop bound taken from
# get_digit_count(k). That is arithmetically impossible for the design measured here:
# a pstm digit is 64 bits, so 255-bit and 256-bit nonces occupy the same four digits and
# run the identical iteration count. See the four-design decomposition in
# results/fix_verification.json (decomposition_4_3_0).
#
# Pinned inputs (verify by sha256 before building; fetch once, then build offline):
#   4-2-1-open.tar.gz  3bbddd70f54ba6c8ec3730cb666af2b7abf617f7468410db094f31b21cd924d2  (pre-fix, vulnerable)
#   4-3-0-open.tar.gz  b6fe9a3c6290ef10169ebf35d65bc7e1ac54ce8f360c6f71bd0630de68c83667  (fix added)
#   4-6-0-open.tar.gz  87be70df27356fec1221011b8ac6f12a4ad1e7e7eaaaf73d73bc94ad9be02dd9  (latest open release)
#
# PROVENANCE CAVEAT: MatrixSSL's upstream repository was withdrawn after the Rambus
# acquisition. These sources are the archived github.com/BlobbyBob/matrixssl mirror,
# tags <ver>-open. This is a mirror, not the vendor, and is recorded as such. CVE is
# CVE-2019-13629.
#
# Build cell: the vendor's own crypto/core static libraries via `make`, with the
# stock configs/default/{crypto,core,matrixssl}Config.h copied into place, offline in
# the ct-toolchain image. USE_CONSTANT_TIME_ECC_MULMOD is on by default from 4.3.0, so
# the patched arms exercise the vendor's shipped constant-time path with no extra flags.
set -euo pipefail
SRC="${1:?usage: acquire.sh <dir-with-verified-tarballs>}"
IMG=localhost/ct-toolchain/gcc-bookworm:1
WORK="$(mktemp -d)"
HERE="$(cd "$(dirname "$0")" && pwd)"

for v in 4-2-1 4-3-0 4-6-0; do
  tar -C "$WORK" -xzf "$SRC/$v-open.tar.gz"
  d="$WORK/matrixssl-$v-open"
  cp "$d/configs/default/cryptoConfig.h"    "$d/crypto/"
  cp "$d/configs/default/coreConfig.h"      "$d/core/"
  cp "$d/configs/default/matrixsslConfig.h" "$d/matrixssl/"
  podman run --rm --network=none -v "$WORK:/w:Z" "$IMG" sh -c \
    "cd /w/matrixssl-$v-open && make -C core >/dev/null && make -C crypto >/dev/null"
  # eccMulmodCt must be present from 4.3.0 (the constant-time fix); absent in 4.2.1.
  podman run --rm -v "$WORK:/w:Z" "$IMG" sh -c \
    "nm -C /w/matrixssl-$v-open/crypto/libcrypt_s.a | grep -c ' T eccMulmodCt' || true"
done

# dudect on the scalar multiplication, 255-bit vs 256-bit nonce, plus the same-length
# control that proves the residual is bit-length dependence and not noise.
for v in 4-2-1 4-3-0 4-6-0; do
  M="matrixssl-$v-open"
  for mode in "" "CONTROL=same"; do
    podman run --rm --network=none -v "$WORK:/w:Z" -v "$HERE/../harness:/h:ro,Z" \
      -v "$(cd "$HERE/../../../src/corpus/score/adapters" && pwd):/driver:ro,Z" \
      localhost/ct-toolchain/dudect:1 sh -c \
      "cd /w && gcc -O2 -I/driver -I$M -I$M/crypto -I$M/core/include -I$M/core/osdep/include -I$M/core \
         -o /tmp/d /h/dudect_mx.c $M/crypto/libcrypt_s.a $M/core/libcore_s.a -lm && \
       env $mode DUDECT_BATCHES=3 DUDECT_MEASUREMENTS=20000 taskset -c 2 /tmp/d 2>&1 | grep 'max t' | tail -1"
  done
done

# Timing traces for the recovery half: sign a fixed digest under random nonces, timed
# with rdtscp, in the Minerva trace format. See evidence/ for committed instances.
for v in 4-2-1 4-3-0; do
  M="matrixssl-$v-open"
  podman run --rm --network=none -v "$WORK:/w:Z" -v "$HERE:/a:ro,Z" "$IMG" sh -c \
    "gcc -O2 -DNSIGS=6000 -I/w/$M -I/w/$M/crypto -I/w/$M/core/include -I/w/$M/core/osdep/include \
       -I/w/$M/core /a/sign_mx.c /w/$M/crypto/libcrypt_s.a /w/$M/core/libcore_s.a -lm -o /tmp/s && \
     taskset -c 2 /tmp/s" > "$WORK/trace-$v.csv"
done
echo "acquired: dudect residual + traces for 4-2-1 / 4-3-0 / 4-6-0"
rm -rf "$WORK"
