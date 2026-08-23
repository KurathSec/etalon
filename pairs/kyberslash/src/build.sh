#!/bin/sh
set -eu
ARM="$1"; OPT="$2"; OUT="$3"; SRC="$(dirname "$0")"
mkdir -p "$OUT"
CFLAGS="-std=c11 -Wall -Wextra -${OPT} -g -fno-lto \
        -ffile-prefix-map=$(cd "$SRC" && pwd)=. -frandom-seed=kyberslash"
# shellcheck disable=SC2086
"${CC:-cc}" $CFLAGS -I"$SRC" -c "$SRC/${ARM}.c" -o "$OUT/coeff_${ARM}.o"
# also a linkable object we can disassemble
"${CC:-cc}" $CFLAGS -I"$SRC" -c "$SRC/${ARM}.c" -o "$OUT/harness_${ARM}"
echo "built $OUT/harness_${ARM}"
