"""The site-local adjudication rule: a tier-C miss by a host-bound (statistical) tool is
unadjudicated, every other outcome passes through unchanged, and the committed verdicts
carry exactly that outcome for the division pair under dudect.
"""
from pathlib import Path
import importlib.util
import json

import pytest

REPO = Path(__file__).resolve().parents[2]


def _score():
    spec = importlib.util.spec_from_file_location("score", REPO / "bin" / "score.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_a_tier_c_miss_by_a_statistical_tool_is_unadjudicated():
    m = _score()
    assert m.adjudicate("missed", "C", "statistical") == "unadjudicated"


@pytest.mark.parametrize("outcome,tier,technique", [
    ("missed", "A", "statistical"), ("missed", "C", "taint"), ("detected", "C", "statistical"),
    ("non_discriminating", "C", "statistical"), ("missed", None, "statistical"),
])
def test_everything_else_passes_through(outcome, tier, technique):
    m = _score()
    assert m.adjudicate(outcome, tier, technique) == outcome


def test_the_committed_division_row_carries_the_status():
    vp = REPO / "results" / "verdicts.jsonl"
    if not vp.exists():
        pytest.skip("no committed verdicts")
    rows = [json.loads(l) for l in vp.read_text().splitlines() if l.strip()]
    row = next(r for r in rows if r["tool"] == "dudect" and r["pair"] == "kyberslash")
    assert row["outcome"] == "unadjudicated"
