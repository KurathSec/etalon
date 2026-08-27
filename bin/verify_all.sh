#!/bin/sh
# Every gate, in order, one line each. This is the single command a reader runs
# from a cold clone to check the artifact behind the paper:
#
#   1. bin/verify.py       the recovery oracle: committed observations become a key
#                          that verifies under the published public key (ORC-1/ORC-2)
#   2. bin/selfcheck.py    every control the repository can currently check
#   3. pytest              the unit tests, which plant defects and assert the gates see them
#   4. bin/paper_check.py  the manuscript consistency rules (skipped when the paper
#                          tree is not present: it is untracked for double-blind review)
#   5. bin/regen.py --headline  must REFUSE to print an aggregate recall figure while
#                          the census is expanded rather than complete. The paper claims
#                          the generator refuses; this line is that claim checked.
#
# Exit status is non-zero if any gate fails. Logs go to $VERIFY_LOG_DIR (default
# ./cache/verify), one file per gate.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PY:-python3}"
LOGS="${VERIFY_LOG_DIR:-$REPO/cache/verify}"
mkdir -p "$LOGS"
rc=0

gate() {
  name="$1"; shift
  log="$LOGS/$name.log"
  if "$@" >"$log" 2>&1; then
    printf 'PASS  %-12s %s\n' "$name" "$*"
  else
    printf 'FAIL  %-12s %s  (see %s)\n' "$name" "$*" "$log"
    rc=1
  fi
}

# A gate whose PASS is a refusal: the command must exit non-zero and say so.
refusal() {
  name="$1"; shift
  log="$LOGS/$name.log"
  if "$@" >"$log" 2>&1; then
    printf 'FAIL  %-12s %s  printed a headline recall figure; it must refuse (see %s)\n' \
      "$name" "$*" "$log"
    rc=1
  elif grep -q "REFUSING to print a headline recall figure" "$log"; then
    printf 'PASS  %-12s %s  refused, as the paper claims\n' "$name" "$*"
  else
    printf 'FAIL  %-12s %s  exited non-zero without the refusal (see %s)\n' \
      "$name" "$*" "$log"
    rc=1
  fi
}

cd "$REPO"
gate oracle    "$PY" bin/verify.py
gate controls  "$PY" bin/selfcheck.py
gate tests     "$PY" -m pytest -q
if [ -d "$REPO/paper/tches" ]; then
  gate paper   "$PY" bin/paper_check.py
else
  printf 'SKIP  %-12s paper/tches is not present in this clone\n' paper
fi
refusal headline "$PY" bin/regen.py --headline

exit $rc
