#!/bin/sh
# Build the paper. Regenerates every number from committed data first, so the PDF
# can never quote a figure that is not currently derivable. The paper source lives
# under paper/, which is gitignored: it is not tracked, so a double-blind
# submission cannot leak through the repository and every number has to come
# through this path rather than through prose.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$REPO/bin/regen.py" --tex "$REPO/paper/tches/numbers.tex"
cd "$REPO/paper/tches"
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
bibtex main >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
echo "built paper/tches/main.pdf"
