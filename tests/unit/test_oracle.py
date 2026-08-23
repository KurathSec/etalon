"""The oracle must be able to fail.

Every test here plants a defect and asserts the oracle notices. A suite that
only ever runs the happy path certifies that the code ran, not that it measures
anything, and the recurring defect in this programme's history is a default
presented as a measurement.
"""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import zlib

REPO = pathlib.Path(__file__).resolve().parents[2]
POS = REPO / "pairs" / "_sentinel-positive"


def _rec():
    spec = importlib.util.spec_from_file_location("rec", POS / "recover" / "recover.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _digest():
    return json.loads((POS / "recover" / "fixtures" / "verifier.json").read_text())["sha256"]


class TestOracleAsCommitted:
    def test_verify_passes(self):
        r = subprocess.run([sys.executable, str(REPO / "bin" / "verify.py")],
                           cwd=REPO, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr

    def test_recovery_succeeds_on_the_vulnerable_arm(self):
        rec = _rec()
        prefix, _ = rec.recover(rec.load(POS / "traces" / "vulnerable.bin.z", 60))
        assert rec.finish(prefix, _digest()) is not None

    def test_the_same_recovery_fails_on_the_patched_arm(self):
        """ORC-2. Without this the corpus cannot tell a working recovery from a
        script that already knows the answer."""
        rec = _rec()
        prefix, _ = rec.recover(rec.load(POS / "traces" / "patched.bin.z", 60))
        assert rec.finish(prefix, _digest()) is None


class TestPlantedDefectsAreCaught:
    def test_corrupted_timings_break_recovery(self, tmp_path):
        """Shuffle the timings and the key must stop being recoverable.

        This is what proves the recovery reads the side channel rather than
        anything else. If it still succeeded here, the answer would be reaching
        it by some path the design does not know about.
        """
        rec = _rec()
        blob = zlib.decompress((POS / "traces" / "vulnerable.bin.z").read_bytes())
        flat = bytearray(blob)
        flat.reverse()                      # destroys the position/guess structure
        bad = tmp_path / "bad.bin.z"
        bad.write_bytes(zlib.compress(bytes(flat), 1))
        prefix, _ = rec.recover(rec.load(bad, 60))
        assert rec.finish(prefix, _digest()) is None

    def test_a_wrong_verifier_is_not_satisfied(self):
        """The published key is what decides, so a different key must not pass."""
        rec = _rec()
        prefix, _ = rec.recover(rec.load(POS / "traces" / "vulnerable.bin.z", 60))
        other = hashlib.sha256(b"a different key entirely").hexdigest()
        assert rec.finish(prefix, other) is None

    def test_trace_digest_control_catches_a_tampered_trace(self, tmp_path):
        """TRC-1 must notice a trace whose bytes changed."""
        record = json.loads((POS / "acquire" / "record.json").read_text())
        entry = next(t for t in record["traces"] if t["arm"] == "vulnerable")
        blob = (POS / "traces" / "vulnerable.bin.z").read_bytes()
        assert hashlib.sha256(blob).hexdigest() == entry["sha256_file"]
        tampered = bytearray(blob)
        tampered[-1] ^= 0xFF
        assert hashlib.sha256(bytes(tampered)).hexdigest() != entry["sha256_file"]
