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
python3 "$REPO/bin/figures.py"
python3 "$REPO/bin/recovery_cards.py"
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
  if ! pdflatex -interaction=nonstopmode -halt-on-error main.tex >/tmp/paperbuild.log 2>&1; then
    echo "build_paper: pdflatex FAILED, main.pdf is unchanged and now stale" >&2
    grep -E "^(!|l\.[0-9])" /tmp/paperbuild.log | head -20 >&2
    exit 1
  fi
}
run_latex
bibtex main >/dev/null 2>&1 || true
run_latex
run_latex

# The PDF must be newer than every source it is built from, or it is not this paper.
newest_src="$(ls -t main.tex numbers.tex sec/*.tex gen/*.tex 2>/dev/null | head -1)"
if [ "$newest_src" -nt main.pdf ]; then
  echo "build_paper: main.pdf is older than $newest_src after a successful build" >&2
  exit 1
fi
echo "built paper/tches/main.pdf"
