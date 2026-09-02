"""The KyberSlash emission map: the generator reproduces its committed record from the
lock, a planted change to the lock moves the map and the finding, and the clause about
levels unsafe under both compilers tracks the intersection rather than a kept sentence.
"""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "bin" / "kyberslash_emission.py"
REC = REPO / "results" / "kyberslash_emission.json"
LOCK = REPO / "locks" / "binaries.lock.json"


def _mod():
    spec = importlib.util.spec_from_file_location("kem", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_check_passes_on_the_committed_record():
    if not REC.exists() or not LOCK.exists():
        pytest.skip("record or lock absent")
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _planted_lock(tmp_path, mutate):
    lock = json.loads(LOCK.read_text())
    mutate(lock["kyberslash"])
    p = tmp_path / "lock.json"
    p.write_text(json.dumps(lock))
    return p


def test_a_planted_count_is_refused_not_absorbed(tmp_path):
    """A lock that contradicts the literal finding stops the generator; the record
    cannot quietly keep a sentence the data no longer supports."""
    if not LOCK.exists():
        pytest.skip("lock absent")
    m = _mod()
    cell = "gcc-12.2.0-Os-x86_64-linux-gnu"

    def mutate(k):
        k[cell]["vulnerable"]["leak_class_instructions"] = 0
    m.LOCK = _planted_lock(tmp_path, mutate)
    with pytest.raises(SystemExit) as e:
        m.build()
    assert "gcc emits it at" in str(e.value) and "rewrite the literal" in str(e.value)


def test_the_unsafe_under_both_clause_is_guarded(tmp_path):
    if not LOCK.exists():
        pytest.skip("lock absent")
    m = _mod()

    def mutate(k):
        # Make clang emit at -Os as gcc does, so -Os joins the intersection.
        k["clang-14.0.6-Os-x86_64-linux-gnu"]["vulnerable"]["leak_class_instructions"] = 1
    m.LOCK = _planted_lock(tmp_path, mutate)
    with pytest.raises(SystemExit) as e:
        m.build()
    assert "unsafe under both" in str(e.value)


def test_the_literal_matches_the_lock_today():
    if not LOCK.exists():
        pytest.skip("lock absent")
    doc = _mod().build()
    for vd, levels in doc["emitting_by_vendor"].items():
        for lv in levels:
            assert "-" + lv in doc["finding"]
