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
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
bibtex main >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
echo "built paper/tches/main.pdf"
