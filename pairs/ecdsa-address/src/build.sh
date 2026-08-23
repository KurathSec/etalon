#!/bin/sh
set -eu
ARM="$1"; OPT="$2"; OUT="$3"; SRC="$(dirname "$0")"
mkdir -p "$OUT"
CFLAGS="-std=c11 -Wall -${OPT} -g -fno-lto -ffile-prefix-map=$(cd "$SRC" && pwd)=. -frandom-seed=ecdsa-nonce"
# shellcheck disable=SC2086
"${CC:-cc}" $CFLAGS -I"$SRC" "$SRC/harness.c" "$SRC/${ARM}.c" -o "$OUT/harness_${ARM}" -lcrypto
echo "built $OUT/harness_${ARM}"
