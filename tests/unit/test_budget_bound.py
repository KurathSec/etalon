"""The MatrixSSL budget bound: the generator reproduces its record, refuses a planted
change, reproduces the worked estimate from the committed dump, and is live on a
synthetic dump whose signal is loud.
"""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "bin" / "matrixssl_budget_bound.py"
REC = REPO / "results" / "matrixssl_budget_bound.json"


def _mod():
    spec = importlib.util.spec_from_file_location("mbb", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_check_passes_on_the_committed_record():
    if not REC.exists() or not (REPO / "results/raw/matrixssl/repeats/4-3-0.bit255.r1.bin.gz").exists():
        pytest.skip("record or dump absent")
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_check_refuses_a_planted_change(tmp_path, monkeypatch):
    if not REC.exists():
        pytest.skip("record absent")
    doc = json.loads(REC.read_text())
    doc["bound"]["rounds"]["2"]["signatures"] *= 10
    planted = tmp_path / "planted.json"
    planted.write_text(json.dumps(doc))
    m = _mod()
    monkeypatch.setattr(m, "OUT", planted)
    monkeypatch.setattr(sys, "argv", ["x", "--check"])
    assert m.main() != 0


def test_worked_estimate_reproduces_from_the_committed_dump():
    m = _mod()
    if not m.DUMP.exists():
        pytest.skip("dump absent")
    cl, t = m._load_dump(m.DUMP)
    meas = m.measured(cl, t)
    b = m.bound(meas["snr"], 90 / 100000)
    assert 0.13 < meas["snr"] < 0.16
    assert 180 < meas["mde_ticks"] < 192
    assert 0.46 < b["oracle_error"] < 0.48
    assert 3e5 < b["rounds"]["1"]["signatures"] < 8e5
    assert 1e11 < b["rounds"]["2"]["signatures"] < 6e11


def test_a_loud_synthetic_signal_gives_a_small_budget():
    m = _mod()
    rng = np.random.default_rng(0)
    n = 20000
    cl = np.concatenate([np.zeros(n, dtype=np.int64), np.ones(n, dtype=np.int64)])
    t = np.concatenate([rng.normal(1e6, 100, n), rng.normal(1e6 + 2000, 100, n)])
    meas = m.measured(cl, t)
    b = m.bound(meas["snr"], 1.0)
    assert meas["snr"] > 10
    assert b["oracle_error"] < 1e-6
    assert b["rounds"]["2"]["signatures"] < 100
