"""The vocabulary firewall must actually fire.

A guarantee that is never tested is a guarantee that silently lapses. These
tests plant each forbidden shape and assert the checker catches it.

This file is exempt from the scan (see the skip list in data/namecheck.toml)
because it plants a canary on purpose.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NAMECHECK = REPO / "bin" / "namecheck.py"


def run_namecheck(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(NAMECHECK), *args],
        capture_output=True, text=True, cwd=REPO,
    )


class TestRepositoryIsClean:
    def test_tracked_files_pass(self):
        result = run_namecheck()
        assert result.returncode == 0, result.stderr


class TestForbiddenShapesAreCaught:
    def _plant(self, tmp_path: Path, text: str) -> subprocess.CompletedProcess:
        (tmp_path / "planted.md").write_text(text, encoding="utf-8")
        return run_namecheck("--paths", str(tmp_path))

    def test_a_registered_term_is_caught(self, tmp_path):
        """Uses a harmless canary rather than a real term.

        The genuine terms are held as digests precisely so they do not appear in
        plaintext in a repository that will become public, and this file will be
        public. Planting a real one here would put back exactly what the digests
        remove.
        """
        result = self._plant(tmp_path, "a line containing namecheckcanary\n")
        assert result.returncode == 1, result.stdout

    def test_an_em_dash_is_caught(self, tmp_path):
        result = self._plant(tmp_path, "a line with an — in it\n")
        assert result.returncode == 1, result.stdout

    def test_ordinary_prose_passes(self, tmp_path):
        result = self._plant(tmp_path, "a line that says nothing forbidden\n")
        assert result.returncode == 0, result.stderr
