#!/usr/bin/env python3
"""dudect adapter: score a pair's arm for a timing leak, PR-4 verdict rule.

Emits a normalised verdict, never a raw score. Two things changed under PR-3:

  * The run goes to a fixed full budget (the driver no longer stops at the first
    crossing), so the recorded max t is a real budget-exhausted value and not a
    first-crossing lower bound mislabelled "budget exhausted".

  * The verdict is a permutation test, not a band. The run dumps its raw
    per-measurement samples; the adapter shuffles their class labels within batch,
    recomputes dudect's maximum |t| over the same crop ladder, and places the
    observed value in that null (bin/dudect_permute.py). The class difference of
    means with a bootstrap 95% CI (bin/dudect_ci.py) is reported beside it as the
    effect size. Absent a usable null the adapter returns an error, never a clean
    reading: PR-4 replaced the calibrated tau band of PR-3 because tau is not
    budget-invariant under the null, so one constant could not serve runs at
    different budgets, and a band fitted on the sentinel harness was being applied
    to harnesses that never shared its noise.

The exit code is never trusted; the verdict comes from the samples and the
committed t-trajectory.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[4]
IMAGE = "localhost/ct-toolchain/dudect:1"
DRIVER = REPO / "src" / "corpus" / "score" / "adapters" / "dudect_driver.c"
CPU = 2   # a P-core; cpuset is undelegated so we taskset inside the container
CALIB = REPO / "results" / "dudect_calibration.json"

_ci_spec = importlib.util.spec_from_file_location("dudect_ci", REPO / "bin" / "dudect_ci.py")
_ci = importlib.util.module_from_spec(_ci_spec)
_ci_spec.loader.exec_module(_ci)


_perm_spec = importlib.util.spec_from_file_location(
    "dudect_permute", REPO / "bin" / "dudect_permute.py")
_perm = importlib.util.module_from_spec(_perm_spec)
_perm_spec.loader.exec_module(_perm)

PERM_ALPHA = 0.05
PERMS = 10000


def _permutation_p(dump: pathlib.Path) -> dict | None:
    """Decide this run against a null built from its own samples.

    Replaces the calibrated tau band, which was not a valid rule: tau = |t|/sqrt(n)
    is not budget-invariant under the null, so one constant cannot serve runs at
    different measurement counts, and a band calibrated on the sentinel harness was
    being applied to harnesses that never shared its noise structure. The null here
    is this run's own labels shuffled within batch, so it is matched to this run's
    budget, harness and noise by construction. Registered in
    preregistration/PR-4-permutation-verdict.md.
    """
    if not dump.exists():
        return None
    try:
        r = _perm.permute(dump, perms=PERMS, n_batches=BATCHES)
    except Exception as exc:                      # a failed null must not pass as clean
        return {"error": str(exc)}
    return None if "error" in r else r


# A uniform budget across every pair, so the null-tau threshold calibrated on the
# negative sentinel transfers: MEASUREMENTS per batch times BATCHES is the same
# total everywhere. Sized so the slow EC pairs finish in a couple of minutes;
# tau is the effect size, so a real leak is resolved well within this budget.
MEASUREMENTS = 20000
BATCHES = 3


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 1800, batches: int | None = None,
          measurements: int | None = None, save_raw: bool = True,
          amp: int | None = None) -> dict:
    """Score one arm. `amp` overrides the pair's compiled-in amplification with
    -DAMP=n, which is what the registered detection curve sweeps; leaving it None
    builds the pair exactly as committed."""
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "dudect.toml").read_text())
    driver = cfg["driver"]
    header = cfg["header"]
    opt = opt or cfg.get("opt", "O2")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    libs = cfg.get("libs", "")
    ampdef = f"-DAMP={int(amp)}" if amp is not None else ""
    outdir = pathlib.Path(tempfile.mkdtemp(prefix="dudect-"))
    nb = batches if batches is not None else BATCHES
    nm = measurements if measurements is not None else MEASUREMENTS
    try:
        result = subprocess.run(
            ["podman", "run", "--rm", "--network=none",
             "-v", f"{src}:/src:ro,Z", "-v", f"{harness}:/harness:ro,Z",
             "-v", f"{DRIVER.parent}:/driver:ro,Z", "-v", f"{outdir}:/out:Z",
             "-e", "DUDECT_RAW_DUMP=/out/raw.bin",
             "-e", f"DUDECT_BATCHES={nb}", "-e", f"DUDECT_MEASUREMENTS={nm}",
             IMAGE, "sh", "-c",
             f"cp /src/{header} /work/ && "
             f"gcc -{opt} {ampdef} -I/work -I/harness -o /work/d "
             f"/driver/{driver} /src/{arm}.c {extra} -lm {libs} 2>/work/cc.err "
             f"|| {{ echo BUILD_FAILED; cat /work/cc.err; exit 3; }}; "
             f"taskset -c {CPU} /work/d"],
            capture_output=True, text=True, timeout=timeout)

        out = result.stdout
        tvals = re.findall(r"max t:\s*([+-]?[0-9.]+(?:[eE][+-]?[0-9]+)?)", out)
        tauvals = re.findall(r"max tau:\s*([0-9.]+(?:[eE][+-]?[0-9]+)?)", out)
        max_t = abs(float(tvals[-1])) if tvals else None
        max_tau = float(tauvals[-1]) if tauvals else None
        dump = outdir / "raw.bin"
        eff = _ci.analyse_path(dump) if dump.exists() else {"effect_ticks": None}

        # The per-batch record counts the harness prints, kept beside the dump so
        # the permutation null shuffles within the batches that were actually run
        # rather than within equal splits of the file (exact only when no delta
        # was dropped). Committed with the dump under the same stem.
        m = re.search(r"DUDECT_BATCH_RECORDS((?:\s+\d+)+)", out)
        meta = None
        if m and dump.exists():
            meta = {"batches": nb, "measurements_per_batch": nm,
                    "records_per_batch": [int(x) for x in m.group(1).split()],
                    "source": "DUDECT_BATCH_RECORDS line printed by dudect_run.h"}
            (outdir / "raw.meta.json").write_text(json.dumps(meta) + "\n")

        perm = _permutation_p(dump)
        if "BUILD_FAILED" in result.stdout or result.returncode == 3:
            status, detail = "error", "driver build failed"
        elif max_t is None:
            status, detail = "error", "no t-statistic emitted"
        elif perm is None or "error" in perm:
            # No null means no verdict. Falling back to a threshold here is how a
            # failed measurement becomes a clean reading, which this corpus refuses.
            status = "error"
            detail = ("permutation null unavailable"
                      + (f": {perm['error']}" if perm and "error" in perm else
                         " (no committed samples for this run)"))
        else:
            excl = bool(eff.get("ci_excludes_zero"))
            eff_s = (f"effect {eff['effect_ticks']:.3f} ticks, 95% CI "
                     f"[{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]"
                     if eff.get("effect_ticks") is not None else "no effect sample")
            pv, obs = perm["p_value"], perm["observed_max_abs_t"]
            sv = (f"max |t|={obs:.1f} against this run's own permutation null "
                  f"(p={pv:.4f}, {perm['permutations']:,} shuffles, "
                  f"null p95={perm['null_max_abs_t_p95']:.2f})")
            if pv <= PERM_ALPHA and excl:
                status = "leak_reported"
                detail = f"{sv}; {eff_s}"
            elif pv > PERM_ALPHA:
                status = "clean"
                detail = f"{sv}: the run does not reject its own null. {eff_s}"
            else:
                status = "inconclusive"
                detail = f"{sv} rejects, but the effect CI straddles zero. {eff_s}"

        raw_committed = None
        if save_raw and amp is None and dump.exists() and status != "error":
            rawdir = REPO / "results" / "raw"
            rawdir.mkdir(parents=True, exist_ok=True)
            dest = rawdir / f"{pair_dir.name}_{arm}.dudect.bin.gz"
            with open(dump, "rb") as fi, gzip.open(dest, "wb") as fo:
                shutil.copyfileobj(fi, fo)
            if meta:
                (rawdir / f"{pair_dir.name}_{arm}.dudect.meta.json").write_text(
                    json.dumps(meta) + "\n")
            raw_committed = str(dest.relative_to(REPO))
        return {
            "adapter": "dudect", "tool": "dudect", "arm": arm, "opt": opt,
            "status": status, "detail": detail,
            "max_t": float(tvals[-1]) if tvals else None,
            # tau is kept as a REPORTED effect size only; it decides nothing (PR-4).
            "max_tau": max_tau,
            # The statistic the VERDICT is decided on, as a field rather than only
            # inside `detail`. It had lived only in the prose string, so a consumer
            # wanting "the paper's statistic" reached for max_t instead, which is
            # dudect's own maximum over every test including the second-order one
            # the permutation rule excludes. On the unamplified message arm the two
            # read 220 and 138; on the eightfold-amplified one, 1901 and 213
            # (results/detection_curve_all.json, hmac-timing vulnerable). Anything
            # downstream must use this one.
            "permutation_max_abs_t": (perm or {}).get("observed_max_abs_t"),
            "permutation_p": (perm or {}).get("p_value"),
            "permutation_shuffles": (perm or {}).get("permutations"),
            "permutation_null_p95": (perm or {}).get("null_max_abs_t_p95"),
            "t_trajectory_n": len(tvals),
            "effect_ticks": eff.get("effect_ticks"),
            "ci_low": eff.get("ci_low"), "ci_high": eff.get("ci_high"),
            "n0": eff.get("n0"), "n1": eff.get("n1"),
            "raw": raw_committed,
            "host": {"kernel": platform.release(), "machine": platform.machine(),
                     "cpu_pinned_to": CPU},
        }
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", required=True)
    ap.add_argument("--arm", required=True, choices=["vulnerable", "patched"])
    ap.add_argument("--opt", default="O2")
    ap.add_argument("--batches", type=int, default=None)
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    r = score(REPO / "pairs" / a.pair, a.arm, a.opt,
              batches=a.batches, save_raw=not a.no_save)
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
