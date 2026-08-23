# Vendored from crocs-muni/minerva

Pinned at the commit in `COMMIT`. Upstream is MIT (`LICENSE.md`).

Committed here (MIT, the author's own code):
- `attack/attack.py`   the lattice HNP attack driver
- `attack/__init__.py`
- `attack/params.json`

NOT committed, fetched into the recovery image at the pinned commit instead:
- `attack/ec.py`  incorporates tinyec (https://github.com/alexmgr/tinyec),
  which is GPL v3. Vendoring it into this MIT-licensed tree would create a
  licence conflict, so it is pulled at image-build time from the pinned commit,
  where it is fixed. See `images/tools/minerva-recover/Containerfile`.
