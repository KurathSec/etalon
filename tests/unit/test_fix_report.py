"""The headline fix-verification numbers must regenerate from the committed dumps.

Two defects motivate this file, both found by pointing the committed tools at the
committed artifact rather than at the live measurement path.

The first is that results/fix_verification.json was assembled by hand. bin/regen.py reads
the paper's headline statistics out of it, so the chain from samples to paper had one link
no script closed: STAT-1 could check that the dumps had not changed, never that the
statistics still described them. bin/fix_report.py --check closes it, and this runs it.

The second is that bin/dudect_ci.py read its dump with np.fromfile and never decompressed.
Dumps are committed compressed and only compressed, while the scoring adapter hands the
loader the uncompressed file a container just wrote, so the bug was invisible in the live
path and certain in any re-run of the artifact: the gzip container parsed as 9-byte
records, 151,040 bytes became 16,782 "measurements", and an effect size came back without
complaint. A guard that only ran on the path that already worked would have proved
nothing, so the planted-misparse test below drives the failing path directly.
"""
import gzip
import json
import pathlib
import subprocess
import sys

import numpy as np
import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "bin"))

DUMP = REPO / "results" / "raw" / "matrixssl" / "mx430_bit255v256.bin.gz"


def _ci():
    import importlib
    import dudect_ci
    return importlib.reload(dudect_ci)


@pytest.mark.skipif(not DUMP.exists(), reason="committed MatrixSSL dumps absent")
def test_ci_loader_reads_the_committed_gz():
    """The loader on the committed form must give the number the paper quotes."""
    C = _ci()
    cl, t = C.load(DUMP)
    committed = (json.loads((REPO / "results" / "fix_verification.json").read_text())
                 ["libraries"]["matrixssl"]["measurements_full_report"]
                 ["designs"]["mx430_bit255v256"])
    assert t.size == committed["measurements"], (
        "the committed dump no longer parses to the measurement count the paper quotes")
    got = C.analyse(cl, t)
    assert got["effect_ticks"] == pytest.approx(committed["effect_ticks"], rel=1e-9)
    assert got["ci_low"] == pytest.approx(committed["ci_low"], rel=1e-9)
    assert got["ci_high"] == pytest.approx(committed["ci_high"], rel=1e-9)


@pytest.mark.skipif(not DUMP.exists(), reason="committed MatrixSSL dumps absent")
def test_ci_loader_refuses_a_misparse_instead_of_returning_a_number():
    """Plant the exact failure the old loader had: read the .gz without decompressing."""
    C = _ci()
    raw = DUMP.read_bytes()
    raw = raw[:len(raw) // 9 * 9]          # the truncation np.fromfile did silently
    a = np.frombuffer(raw, dtype=C.REC)
    assert a.size and a.size != gzip.open(DUMP, "rb").read().__len__() // 9, (
        "the planted misparse did not actually differ from the real parse")
    with pytest.raises(ValueError):
        C._checked(a, DUMP)


@pytest.mark.skipif(not DUMP.exists(), reason="committed MatrixSSL dumps absent")
def test_fix_report_reproduces_the_committed_block():
    """Every committed MatrixSSL design must fall out of the dumps again.

    This is the slow one: ten designs, ten thousand permutations each. It is worth its
    runtime because it is the only check that the paper's headline statistics still
    follow from the samples, rather than from a file someone edited.
    """
    r = subprocess.run([sys.executable, str(REPO / "bin" / "fix_report.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "reproduce the committed block exactly" in r.stdout


def test_paper_consistency_rules_are_not_vacuous(tmp_path):
    """The retired-claim scan must catch a claim split across a line break.

    This is the shape the rule exists for: LaTeX sources wrap, so a withdrawn claim
    survives in an appendix with a newline in the middle of it. A literal substring test
    passes over exactly that, which is how a control ends up decorating a defect instead of
    catching it. Round 8 of the blind panel found the real instance by hand; this makes sure
    the machine finds the next one.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("paper_check", REPO / "bin" / "paper_check.py")
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)

    paper = REPO / "paper" / "tches"
    if not (paper / "numbers.tex").exists():
        pytest.skip("paper sources absent")

    import tomllib
    spec_file = REPO / "data" / "paper_consistency.toml"
    rules = tomllib.loads(spec_file.read_text())
    assert rules.get("retired"), "no retired-claim rules to test"
    phrase = rules["retired"][0]["phrase"]

    # Clean tree: the rules pass over what is actually committed.
    assert pc._consistency(_committed_texts(paper), paper) == []

    # Plant the retired claim, wrapped mid-phrase the way a .tex file would wrap it.
    words = phrase.split()
    wrapped = " ".join(words[: len(words) // 2]) + "\n" + " ".join(words[len(words) // 2 :])
    planted = {"sec/planted.tex": f"Some prose. {wrapped} More prose.\n"}
    hits = pc._consistency(planted, paper)
    assert any("planted.tex" in h for h in hits), (
        "the retired-claim scan missed a claim split across a line break")

def _committed_texts(paper):
    """The paper's real sources, keyed as bin/paper_check.py keys them.

    Both tests below asserted that "the committed tree should be clean" while passing an
    empty dict, which asserts nothing: a rule that scans no files finds nothing whatever
    it would have found. That is the failure class this file exists to test for, one
    level out. The [[once]] rules exposed it, because a claim that must appear exactly
    once appears zero times in an empty corpus.
    """
    return {str(f.relative_to(paper)): f.read_text(errors="replace")
            for f in sorted(list(paper.rglob("*.tex")) + list(paper.rglob("*.bib")))}


def test_paper_consistency_survives_markup_and_capitalisation():
    r"""A retired claim must not hide behind \emph{}, \texttt{} or a capital letter.

    Three normalisation bugs have each let this control report clean over a real defect.
    First a literal substring test missed a claim split across a line break. Then a
    whitespace-only test missed one whose words were wrapped in inline font commands: a
    block promoted into the body survived verbatim in an appendix while the rule passed.
    Then case: the surviving copy opened "An \emph{instruction-class} verdict" against a
    rule written "an instruction-class verdict", and capitalisation alone was enough.

    This plants all three at once. A control that has been fooled three times earns a test
    that stays.
    """
    import importlib.util
    import tomllib
    spec = importlib.util.spec_from_file_location("paper_check", REPO / "bin" / "paper_check.py")
    pc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pc)

    paper = REPO / "paper" / "tches"
    if not (paper / "numbers.tex").exists():
        pytest.skip("paper sources absent")

    rules = tomllib.loads((REPO / "data" / "paper_consistency.toml").read_text())["retired"]
    target = next((r for r in rules if "instruction-class verdict" in r["phrase"]), None)
    if target is None:
        pytest.skip("the markup-bearing rule is no longer present")

    assert pc._consistency(_committed_texts(paper), paper) == [], \
        "the committed tree should be clean"

    words = target["phrase"].split()
    # capitalise the opening word, wrap two words in font commands, and wrap a line
    planted = (words[0].capitalize() + " \\emph{" + words[1] + "} " + " ".join(words[2:4])
               + "\n" + " ".join(words[4:-1]) + " \\texttt{" + words[-1] + "}")
    hits = pc._consistency({"sec/planted.tex": f"Prose. {planted} more prose.\n"}, paper)
    assert any("planted.tex" in h for h in hits), (
        "the retired-claim scan missed a claim wrapped in markup and recapitalised")
