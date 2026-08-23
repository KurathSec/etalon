#!/bin/sh
# Build one arm of this pair. Runs inside a toolchain cell image, with no
# network, so the only inputs are the pinned image, these sources and the flags.
#
# usage: build.sh <arm> <optlevel> <outdir>
set -eu
ARM="$1"; OPT="$2"; OUT="$3"
SRC="$(dirname "$0")"
mkdir -p "$OUT"

# Declared once so the arms cannot drift apart in a flag. The prefix map and the
# fixed epoch keep local paths and timestamps out of the binary, which serves
# reproducibility and anonymity at the same time.
CFLAGS="-std=c11 -Wall -Wextra -${OPT} -g -fno-lto \
        -ffile-prefix-map=$(cd "$SRC" && pwd)=. -frandom-seed=sentinel-negative"

# shellcheck disable=SC2086
"${CC:-cc}" $CFLAGS -I"$SRC" \
    "$SRC/harness.c" "$SRC/work.c" "$SRC/${ARM}.c" \
    -o "$OUT/harness_${ARM}"
echo "built $OUT/harness_${ARM}"
