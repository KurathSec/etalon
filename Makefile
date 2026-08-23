# The two entry points that matter, and the line between them.
#
# `verify` is the deliverable. It runs from a cold clone with a stock
# interpreter: no containers, no analysers, no hardware, no network. If it ever
# needs any of those, the platform-bound and portable halves of the oracle have
# leaked into each other.
#
# `acquire` is the other half. It needs podman, a pinned toolchain cell and the
# ability to pin a core, it is run rarely, and its output is committed.

PY ?= python3

.PHONY: verify check test acquire numbers rebuild-check clean

verify:
	$(PY) bin/verify.py

rebuild-check:
	$(PY) bin/build.py --check

check:
	$(PY) bin/namecheck.py
	$(PY) bin/selfcheck.py
	$(PY) bin/export.py --profile anon --check
	$(PY) bin/regen.py
	$(PY) bin/paper_check.py

test:
	$(PY) -m pytest -q

numbers:
	$(PY) bin/regen.py --tex paper/tches/numbers.tex

acquire:
	@echo "Platform-bound. Needs podman and a pinned core. Per pair:"
	@echo "  bash pairs/<id>/acquire/acquire.sh"

clean:
	rm -rf cache/build dist
