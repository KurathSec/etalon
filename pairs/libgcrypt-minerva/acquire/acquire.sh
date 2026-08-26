#!/usr/bin/env bash
# Acquisition for libgcrypt-minerva (tier A). Platform-bound, run rarely; the
# committed traces are its output. Builds two real libgcrypt versions one patch
# apart from their pinned source tarballs, offline, then times ECDSA signatures
# on this host under random nonces. libgcrypt 1.8.4 is the Minerva-vulnerable
# build (CVE-2019-13627); 1.8.5 carries the fix. The verification half
# (recover/recover.py against the committed traces) is portable and runs in CI.
#
# Pinned inputs (verify by sha256 before building; fetch once, then build with
# --network=none):
#   libgpg-error-1.36.tar.bz2  babd98437208c163175c29453f8681094bcaf92968a15cafb1a276076b33c97c
#   libgcrypt-1.8.4.tar.bz2    f638143a0672628fde0cad745e9b14deb85dffb175709cacc1f4fe24b93f2227
#   libgcrypt-1.8.5.tar.bz2    3b4a2a94cb637eff5bdebbcaf46f4d95c4f25206f459809339cdada0eb577ac3
# Upstream: https://gnupg.org/ftp/gcrypt/libgcrypt/ and .../libgpg-error/
#
# Build cell: gcc in the offline ct-toolchain image, ./configure --enable-static
# --disable-shared --disable-asm (so the timing reflects the portable C divider
# and scalar multiplication, not a hand-tuned asm path), CFLAGS=-O2.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="${1:?usage: acquire.sh <dir-with-verified-tarballs> [nsigs]}"
NSIGS="${2:-6000}"
IMG=localhost/ct-toolchain/gcc-bookworm:1
WORK="$(mktemp -d)"

# The image has make/gcc/perl but not bzip2/autotools helpers we rely on the host
# for, so extract on the host, build offline in the image.
for t in libgpg-error-1.36 libgcrypt-1.8.4 libgcrypt-1.8.5; do
  tar -C "$WORK" -xjf "$SRC/$t.tar.bz2"
done

build() { # <srcdir> <prefix> <extra-configure-args...>
  local s="$1"; local p="$2"; shift 2
  podman run --rm --network=none -v "$WORK:/w:Z" "$IMG" sh -c \
    "cd /w/$s && ./configure --prefix=/w/$p $* >/dev/null && make -j\$(nproc) >/dev/null && make install >/dev/null"
}
build libgpg-error-1.36 inst --enable-shared
for v in 1.8.4 1.8.5; do
  build "libgcrypt-$v" "gcry-$v" --enable-static --disable-shared --disable-asm \
        --with-libgpg-error-prefix=/w/inst
done

# One signing harness, linked against each version's static libgcrypt. It signs
# a fixed digest (sha256 of 0x5a repeated) under fresh random nonces, timing each
# gcry_pk_sign with rdtscp, and emits the Minerva attack's trace format.
for v in 1.8.4 1.8.5; do
  arm=$([ "$v" = 1.8.4 ] && echo vulnerable || echo patched)
  podman run --rm --network=none -v "$WORK:/w:Z" -v "$HERE:/h:ro,Z" "$IMG" sh -c \
    "gcc -O2 -DNSIGS=$NSIGS -I/w/gcry-$v/include -I/w/inst/include /h/sign_harness.c \
       /w/gcry-$v/lib/libgcrypt.a -L/w/inst/lib -lgpg-error -lpthread -ldl -o /w/sign-$v && \
     LD_LIBRARY_PATH=/w/inst/lib taskset -c 2 /w/sign-$v" > "$WORK/$arm.csv"
  python3 - "$WORK/$arm.csv" "$HERE/../traces/$arm.csv.z" <<'PY'
import sys, zlib, pathlib
pathlib.Path(sys.argv[2]).write_bytes(zlib.compress(pathlib.Path(sys.argv[1]).read_bytes(), 9))
PY
done

# Optional: the acquisition-side timing measurement recorded in record.json checks
# that the deployed scalar-multiplication primitive is timeable and whether the
# public API discriminates the builds (it does not). ecmul_timing_probe.c times
# the public gcry_mpi_ec_mul over a short-vs-full scalar against each version's
# static lib; see record.json for what it does and does not show.
echo "acquired: traces/vulnerable.csv.z traces/patched.csv.z"
rm -rf "$WORK"
