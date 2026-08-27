#!/bin/sh
# Build the paper. Regenerates every number and every figure from committed data
# first, so the PDF can never quote a figure or a plot that is not currently
# derivable. The paper source lives under paper/, which is gitignored: it is not
# tracked, so a double-blind submission cannot leak through the repository and
# every number has to come through this path rather than through prose.
#
# The paper targets iacrtrans. That class is present, but two of its dependencies
# (sectsty, floatrow) are absent from this TeX installation and tlmgr refuses to
# install them, so they are fetched from the TeX Live tlnet archive on demand.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
TCHES="$REPO/paper/tches"

python3 "$REPO/bin/regen.py" --tex "$TCHES/numbers.tex"
python3 "$REPO/bin/regen.py" --provenance "$TCHES/gen/provenance-table.tex"
python3 "$REPO/bin/figures.py"
python3 "$REPO/bin/recovery_cards.py"
python3 "$REPO/bin/listing.py"
python3 "$REPO/bin/survey_table.py"
python3 "$REPO/bin/index_table.py"
python3 "$REPO/bin/analyser_table.py"
python3 "$REPO/bin/capability_table.py"
python3 "$REPO/bin/controls_table.py"

for pkg in sectsty floatrow; do
  if [ ! -f "$TCHES/$pkg.sty" ] && ! kpsewhich "$pkg.sty" >/dev/null 2>&1; then
    tmp="$(mktemp -d)"
    for base in https://mirrors.rit.edu/CTAN https://mirror.ctan.org; do
      if curl -sSL --max-time 40 -o "$tmp/$pkg.tar.xz" \
           "$base/systems/texlive/tlnet/archive/$pkg.tar.xz" 2>/dev/null \
         && tar -C "$tmp" -xf "$tmp/$pkg.tar.xz" 2>/dev/null \
         && cp "$tmp/tex/latex/$pkg/$pkg.sty" "$TCHES/" 2>/dev/null; then
        break
      fi
    done
    rm -rf "$tmp"
  fi
done

cd "$TCHES"

# Fail loudly. A silent LaTeX failure leaves the PREVIOUS main.pdf in place, and every
# downstream check then reads that stale file: pdfinfo reports its page count, grep finds
# no undefined references in its log, pdftotext finds no NA in its text. Each of those
# reads as a pass. The paper went several rounds of edits in that state once, because the
# build error was sent to /dev/null and nothing compared the PDF's age to its sources.
run_latex() {
  if ! pdflatex -interaction=nonstopmode -halt-on-error "$1.tex" >/tmp/paperbuild.log 2>&1; then
    echo "build_paper: pdflatex FAILED on $1, $1.pdf is unchanged and now stale" >&2
    grep -E "^(!|l\.[0-9])" /tmp/paperbuild.log | head -20 >&2
    exit 1
  fi
}

# Two targets from one source tree: main is the TCHES submission, body only, because
# the venue counts appendices against a twenty-page cap; main-eprint is the same body
# with the appendices restored. Both are built every time. Building only one lets the
# other rot, and a stale eprint is exactly the failure DOC-1 was written to catch.
build_one() {
  run_latex "$1"
  bibtex "$1" >/dev/null 2>&1 || true
  # bibtex tolerates a malformed entry: it reports the problem, DROPS the rest of that
  # entry, and exits successfully, and this line used to end in `|| true`. A duplicate
  # key shipped that way and the only trace was one line in the .blg nobody read.
  if grep -qE "^I was expecting|^I'm skipping|Repeated entry|There (was|were) [0-9]+ error" "$1.blg"; then
    echo "build_paper: bibtex reported a problem in $1.blg:" >&2
    grep -E "^I was expecting|^I'm skipping|Repeated entry|error message" "$1.blg" | head -5 >&2
    exit 1
  fi
  run_latex "$1"
  run_latex "$1"
  # A dangling cross-reference renders as ?? and no other gate sees it. The split makes
  # it easy to write: a body sentence pointing at a label that exists only in the eprint.
  if grep -q "LaTeX Warning: Reference" "$1.log"; then
    echo "build_paper: $1 has dangling reference(s):" >&2
    grep -o "Reference \`[^']*'" "$1.log" | sort -u | head -10 >&2
    exit 1
  fi
  # The PDF must be newer than every source it is built from, or it is not this paper.
  newest_src="$(ls -t "$1.tex" numbers.tex shared/*.tex sec/*.tex gen/*.tex 2>/dev/null | head -1)"
  if [ "$newest_src" -nt "$1.pdf" ]; then
    echo "build_paper: $1.pdf is older than $newest_src after a successful build" >&2
    exit 1
  fi
  echo "built paper/tches/$1.pdf"
}

build_one main
build_one main-eprint
