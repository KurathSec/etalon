"""Every consistency rule in data/paper_consistency.toml must be live, not decorative.

A rule added without watching it fail on a planted defect is decoration. This test plants
each retired phrase (wrapped across a line, the way LaTeX sources wrap), each once-phrase
in two files, and each forbidden phrase in its forbidden file, and asserts the checker
reports every one. It runs over the rules as committed, so a new rule is tested the moment
it is added.
"""
from pathlib import Path
import importlib.util
import tomllib

import pytest

REPO = Path(__file__).resolve().parents[2]


def _pc():
    spec = importlib.util.spec_from_file_location("paper_check", REPO / "bin" / "paper_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rules():
    return tomllib.loads((REPO / "data" / "paper_consistency.toml").read_text())


def _wrap(phrase: str) -> str:
    w = phrase.split()
    return " ".join(w[: len(w) // 2]) + "\n" + " ".join(w[len(w) // 2:])


@pytest.mark.parametrize("entry", _rules().get("retired", []), ids=lambda e: e["phrase"][:40])
def test_every_retired_phrase_is_caught_when_planted(entry):
    pc = _pc(); paper = REPO / "paper" / "tches"
    if not (paper / "numbers.tex").exists():
        pytest.skip("paper sources absent")
    planted = {"sec/planted.tex": f"Some prose. {_wrap(entry['phrase'])} More prose.\n"}
    hits = pc._consistency(planted, paper)
    assert any("planted.tex" in h and "retired" in h for h in hits), entry["phrase"]


@pytest.mark.parametrize("entry", _rules().get("once", []), ids=lambda e: e["phrase"][:40])
def test_every_once_phrase_is_caught_when_stated_twice(entry):
    pc = _pc(); paper = REPO / "paper" / "tches"
    if not (paper / "numbers.tex").exists():
        pytest.skip("paper sources absent")
    planted = {"sec/planted-a.tex": f"A. {entry['phrase']} A.\n",
               "sec/planted-b.tex": f"B. {_wrap(entry['phrase'])} B.\n"}
    hits = pc._consistency(planted, paper)
    assert any("planted" in h for h in hits), entry["phrase"]


@pytest.mark.parametrize("entry", _rules().get("forbidden", []), ids=lambda e: e["phrase"][:40])
def test_every_forbidden_phrase_is_caught_in_its_file(entry):
    pc = _pc(); paper = REPO / "paper" / "tches"
    if not (paper / "numbers.tex").exists():
        pytest.skip("paper sources absent")
    for f in entry["in_files"]:
        planted = {f: f"Prose. {entry['phrase']} Prose.\n"}
        hits = pc._consistency(planted, paper)
        assert any(f in h and "forbidden" in h for h in hits), (entry["phrase"], f)
