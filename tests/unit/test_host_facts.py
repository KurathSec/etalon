"""The host record excuses exactly the drift it states, and nothing else.

A fact in results/host.json is the one the committed dumps were acquired under, not a
description of the machine today, so a later change to the machine is recorded rather
than re-captured. These plant each way that could go wrong: an unstated drift, a drift
that moved again since it was stated, a block that misstates what was acquired, and a
different machine altogether.
"""
from pathlib import Path
import importlib.util
import json
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
K_ACQ = "7.1.8-200.fc44.x86_64"
K_NOW = "7.1.12-200.fc44.x86_64"
K_NEXT = "7.2.0-100.fc45.x86_64"


def _mod():
    spec = importlib.util.spec_from_file_location("host_facts", REPO / "bin" / "host_facts.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _check(tmp_path, committed, fresh):
    m = _mod()
    p = tmp_path / "host.json"
    p.write_text(json.dumps(committed))
    m.OUT = p
    m.capture = lambda: dict(fresh)
    sys.argv = ["host_facts.py", "--check"]
    return m.main()


def _committed(**over):
    d = {"cpu_model": "a model", "governor": "performance", "kernel": K_ACQ}
    d.update(over)
    return d


def _stated(acquired=K_ACQ, now=K_NOW):
    return {"kernel": {"acquired_under": acquired, "now": now, "noticed_utc": "2026-09-10"}}


def test_a_stated_drift_passes(tmp_path):
    committed = _committed(_drift_since_acquisition=_stated())
    assert _check(tmp_path, committed, _committed(kernel=K_NOW)) == 0


def test_an_unstated_drift_fails(tmp_path):
    assert _check(tmp_path, _committed(), _committed(kernel=K_NOW)) == 1


def test_a_drift_that_moved_again_fails(tmp_path):
    committed = _committed(_drift_since_acquisition=_stated())
    assert _check(tmp_path, committed, _committed(kernel=K_NEXT)) == 1


def test_a_block_that_misstates_the_acquired_value_fails(tmp_path):
    committed = _committed(_drift_since_acquisition=_stated(acquired="7.0.0-1.fc44.x86_64"))
    assert _check(tmp_path, committed, _committed(kernel=K_NOW)) == 1


def test_a_field_outside_the_block_still_fails(tmp_path):
    committed = _committed(_drift_since_acquisition=_stated())
    fresh = _committed(kernel=K_NOW, governor="schedutil")
    assert _check(tmp_path, committed, fresh) == 1


def test_a_different_machine_is_not_drift(tmp_path):
    assert _check(tmp_path, _committed(), _committed(cpu_model="another model")) == 2


def test_the_committed_record_states_its_own_drift():
    d = json.loads((REPO / "results" / "host.json").read_text())
    block = d.get("_drift_since_acquisition", {})
    for field, said in block.items():
        assert d[field] == said["acquired_under"], (
            f"{field}: the record's value is not what its drift block calls the acquired one")
        assert said["now"] != said["acquired_under"] and said.get("noticed_utc")
