#!/usr/bin/env bash
# The positive control a referee asked for: the identical timing-ordered lattice
# pipeline that fails on the fixed MatrixSSL build, run on the committed 4.2.1
# pre-fix trace (6,000 signatures) at the same three lattice dimensions. If it
# recovers there, the pipeline is sound and the fixed build's failure is the
# residual's depth; if it does not, the paper must say so.
# Usage: matrixssl_prefix_control.sh            (CPU-heavy: BKZ inside the pinned image)
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TRACE="$REPO/pairs/matrixssl-minerva/evidence/trace-4-2-1.csv.z"
OUT="$REPO/results/raw/matrixssl/lattice-prefix"
mkdir -p "$OUT"
for dim in 90 110 130; do
  f="$OUT/mx-lattice-prefix-6000-d$dim.json"
  if [ -f "$f" ]; then echo "  d$dim: exists"; continue; fi
  # recover.py exits 1 on a miss, which is a result here, not a failure.
  python3 "$REPO/pairs/matrixssl-minerva/recover/recover.py" --trace "$TRACE" \
    --params "{\"dimension\": $dim}" --json > "$f.tmp" || true
  python3 -c "import json; json.load(open('$f.tmp'))" && mv "$f.tmp" "$f"
  python3 -c "import json,sys; d=json.load(open('$f')); print('  d$dim:', d['outcome'], 'budget', d['budget'], 'in', d['elapsed_s'], 's')"
done
echo "matrixssl_prefix_control: records under $OUT"
