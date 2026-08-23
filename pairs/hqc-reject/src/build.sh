#!/bin/sh
set -eu
ARM="$1"; OPT="$2"; OUT="$3"; SRC="$(dirname "$0")"
mkdir -p "$OUT"
CFLAGS="-std=c11 -Wall -${OPT} -g -fno-lto -ffile-prefix-map=$(cd "$SRC" && pwd)=. -frandom-seed=hqc-reject"
"${CC:-cc}" $CFLAGS -I"$SRC" "$SRC/harness.c" "$SRC/${ARM}.c" -o "$OUT/harness_${ARM}"
echo "built $OUT/harness_${ARM}"
