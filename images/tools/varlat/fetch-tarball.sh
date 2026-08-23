#!/bin/sh
# Fetch the valgrind 3.22.0 tarball into the build context, pinned by sha256.
# It is not committed (16 MB, reproducible); the patch and the sha256 are.
set -eu
DIR="$(dirname "$0")/vendor-varlat"
URL="https://sourceware.org/pub/valgrind/valgrind-3.22.0.tar.bz2"
curl -sSL --max-time 180 -o "$DIR/valgrind-3.22.0.tar.bz2" "$URL"
cd "$DIR" && sha256sum -c valgrind.sha256 && echo "tarball verified"
