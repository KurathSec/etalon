#!/usr/bin/env python3
"""dudect adapter: score a pair's arm for a timing leak, PR-3 verdict rule.

Emits a normalised verdict, never a raw score. Two things changed under PR-3:

  * The run goes to a fixed full budget (the driver no longer stops at the first
    crossing), so the recorded max t is a real budget-exhausted value and not a
    first-crossing lower bound mislabelled "budget exhausted".

  * The verdict is not a fixed band. The run dumps its raw per-measurement
    samples; the adapter computes the class difference of means in ticks with a
    bootstrap 95% CI (bin/dudect_ci.py), and decides leak/clean against a null
    band calibrated on the constant-time negative sentinel
    (results/dudect_calibration.json). Absent a calibration file the adapter
    falls back to dudect's own |t| > 10 semantics and says so.

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


def _null_threshold() -> tuple[float, str, str]:
    """Return (threshold, statistic, basis). dudect's tau = t / sqrt(n) is
    budget-invariant, so a tau threshold calibrated on the negative sentinel
    transfers to pairs run at different measurement counts; before calibration
    exists, fall back to dudect's own |t| > 10."""
    if CALIB.exists():
        c = json.loads(CALIB.read_text())
        return float(c["null_threshold_tau"]), "tau", "calibrated on the negative sentinel"
    return 10.0, "t", "provisional (dudect native |t|>10; no calibration yet)"


# A uniform budget across every pair, so the null-tau threshold calibrated on the
# negative sentinel transfers: MEASUREMENTS per batch times BATCHES is the same
# total everywhere. Sized so the slow EC pairs finish in a couple of minutes;
# tau is the effect size, so a real leak is resolved well within this budget.
MEASUREMENTS = 20000
BATCHES = 3


def score(pair_dir: pathlib.Path, arm: str, opt: str | None = None,
          timeout: int = 1800, batches: int | None = None,
          measurements: int | None = None, save_raw: bool = True) -> dict:
    src = pair_dir / "src"
    harness = pair_dir / "harness"
    cfg = tomllib.loads((harness / "dudect.toml").read_text())
    driver = cfg["driver"]
    header = cfg["header"]
    opt = opt or cfg.get("opt", "O2")
    extra = " ".join(f"/src/{s}" for s in cfg.get("extra_sources", []))
    libs = cfg.get("libs", "")
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
             f"gcc -{opt} -I/work -I/harness -o /work/d "
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

        thr, stat, basis = _null_threshold()
        val = max_tau if stat == "tau" else max_t
        if "BUILD_FAILED" in result.stdout or result.returncode == 3:
            status, detail = "error", "driver build failed"
        elif max_t is None or val is None:
            status, detail = "error", "no t-statistic emitted"
        else:
            excl = bool(eff.get("ci_excludes_zero"))
            eff_s = (f"effect {eff['effect_ticks']:.3f} ticks, 95% CI "
                     f"[{eff['ci_low']:.3f}, {eff['ci_high']:.3f}]"
                     if eff.get("effect_ticks") is not None else "no effect sample")
            sv = f"{stat}={val:.3g}" if stat == "tau" else f"|t|={val:.0f}"
            if val > thr and excl:
                status = "leak_reported"
                detail = f"{sv} > null band {thr:.3g} ({basis}); {eff_s}"
            elif val <= thr:
                status = "clean"
                detail = (f"{sv} within null band {thr:.3g} ({basis}); "
                          f"within the constant-time sentinel's null. {eff_s}")
            else:
                status = "inconclusive"
                detail = f"{sv} > null band {thr:.3g} but the effect CI straddles zero. {eff_s}"

        raw_committed = None
        if save_raw and dump.exists() and status != "error":
            rawdir = REPO / "results" / "raw"
            rawdir.mkdir(parents=True, exist_ok=True)
            dest = rawdir / f"{pair_dir.name}_{arm}.dudect.bin.gz"
            with open(dump, "rb") as fi, gzip.open(dest, "wb") as fo:
                shutil.copyfileobj(fi, fo)
            raw_committed = str(dest.relative_to(REPO))
        return {
            "adapter": "dudect", "tool": "dudect", "arm": arm, "opt": opt,
            "status": status, "detail": detail,
            "max_t": float(tvals[-1]) if tvals else None,
            "max_tau": max_tau,
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
