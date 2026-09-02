"""The MatrixSSL mechanism ablation: each patch rewrites exactly the dummy blocks it names
and refuses a source without them; the generator reproduces its committed record and
refuses a planted change to a per-run delta.
"""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "bin" / "matrixssl_ablation.py"
REC = REPO / "results" / "matrixssl_ablation.json"
RAW = REPO / "results" / "raw" / "matrixssl" / "ablation"


def _mod():
    spec = importlib.util.spec_from_file_location("mxa", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _miniature(m):
    """A stand-in for eccMulmodCt carrying every anchor the patches key on."""
    block = ("        if (mode == 0 && i == 0)\n        {\n            /* Dummy operations. */\n"
             "            " + m.DUMMY_BLOCK + "\n            if (err != PS_SUCCESS)\n            {\n"
             "                goto done;\n            }\n            continue;\n        }\n")
    return ("int32_t eccMulmodCt(psPool_t *pool)\n{\n    psEccPoint_t *tG, *M[3];\n"
            "    for (i = 0; i < 3; i++)\n    {\n    }\n    " + m.INIT_ANCHOR +
            "\n    for (;; )\n    {\n" + block + block.replace("i == 0", "i == 1") +
            "    }\n    for (i = 0; i < 3; i++)\n    {\n    }\n}\n"
            "# endif /* USE_CONSTANT_TIME_ECC_MULMOD */\n")


def test_each_patch_changes_only_what_it_names():
    m = _mod()
    src = _miniature(m)
    fn = src[src.index("int32_t eccMulmodCt("):src.index("# endif")]
    assert m.patch_orig(fn) == fn
    nop = m.patch_nop(fn)
    assert "eccProjectiveDblPoint(pool,\n                    M[1], M[2]" not in nop
    assert nop.count("ablation: no dummy operations") == 2
    inplace = m.patch_inplace(fn)
    assert inplace.count("M[2], M[2],") == 2 and inplace.count("M[0], M[1], M[2],") == 2
    assert "M[5]" not in inplace
    ev = m.patch_evolving(fn)
    assert ev.count("M[3], M[4], M[4],") == 2 and ev.count("M[3], M[3],") == 2
    assert "*M[5]" in ev and ev.count("i < 5") == 2 and ev.count("pstm_copy(&M[1]->z, &M[4]->z)") == 1
    evo = m.patch_evolvingoop(fn)
    assert evo.count("M[3], M[2],") == 2 and evo.count("swp = M[3]") == 2


def test_a_patch_refuses_a_source_without_its_anchors():
    m = _mod()
    with pytest.raises(SystemExit):
        m.patch_inplace("int32_t eccMulmodCt(void) { return 0; }")


def test_check_passes_on_the_committed_record():
    if not REC.exists() or not any(RAW.glob("*.bin.gz")):
        pytest.skip("record or dumps absent")
    r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_a_planted_delta_fails_the_check(tmp_path):
    if not REC.exists() or not any(RAW.glob("*.bin.gz")):
        pytest.skip("record or dumps absent")
    m = _mod()
    rec = json.loads(REC.read_text())
    rec["runs"][0]["delta_ticks"] += 1000.0
    planted = tmp_path / "rec.json"
    planted.write_text(json.dumps(rec))
    m.OUT = planted
    sys.argv = [str(GEN), "--check"]
    assert m.main() == 1
