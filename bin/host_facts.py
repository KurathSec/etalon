#!/usr/bin/env python3
"""Capture the acquisition host's facts into results/host.json.

Every timing number in this repository is host-conditional, so the host is part of
the result and must be recorded the way any other measurement is: by a program, from
the machine, not typed. An earlier revision of host.json was hand-captured, which is
the one input to the paper's numbers that no script could regenerate.

Two facts matter beyond the model string and are recorded here because a reviewer
cannot otherwise check them:

  * The core TYPE the measurements pin to. This host is hybrid (Intel performance and
    efficiency cores with different microarchitectures and different dividers), so
    "we pinned to core 2" is not reproducible information unless the type is named.
  * The DOITM state (IA32_UARCH_MISC_CTL bit 0), which governs whether the vendor
    offers data-independent timing at all. Reading it needs privileges we do not take;
    when it cannot be read we say so rather than assuming a default. Integer division
    is outside the DOITM guarantee regardless, which is why the division measurements
    do not rest on this bit.

Usage: bin/host_facts.py [--check]
  --check re-captures and reports whether the committed file still matches this host.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "host.json"
PINNED_CPU = 2   # the core every timing acquisition tasksets onto


def _cpuinfo() -> dict:
    txt = pathlib.Path("/proc/cpuinfo").read_text()
    first = txt.split("\n\n")[0]
    got = {}
    for line in first.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            got[k.strip()] = v.strip()
    return got


def _expand(mask: str) -> set[int]:
    out: set[int] = set()
    for part in mask.strip().split(","):
        if "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def _core_type(cpu: int) -> tuple[str, bool]:
    """(type of this cpu, whether the machine is hybrid)."""
    core = pathlib.Path("/sys/devices/cpu_core/cpus")
    atom = pathlib.Path("/sys/devices/cpu_atom/cpus")
    if core.exists() and atom.exists():
        if cpu in _expand(core.read_text()):
            return "performance", True
        if cpu in _expand(atom.read_text()):
            return "efficiency", True
        return "unknown", True
    return "uniform", False


def _read(path: str) -> str | None:
    p = pathlib.Path(path)
    try:
        return p.read_text().strip()
    except OSError:
        return None


def _doitm(cpu: int) -> str:
    """DOITM bit, or why it is not known. Never guessed."""
    try:
        with open(f"/dev/cpu/{cpu}/msr", "rb") as f:
            f.seek(0x1B01)                       # IA32_UARCH_MISC_CTL
            v = struct.unpack("<Q", f.read(8))[0]
        return f"enabled (bit 0 set)" if v & 1 else "disabled (bit 0 clear)"
    except PermissionError:
        return "not read: /dev/cpu/N/msr requires elevated privileges, not taken here"
    except FileNotFoundError:
        return "not read: msr device absent (module not loaded)"
    except OSError as e:
        return f"not read: {type(e).__name__}"


def capture() -> dict:
    ci = _cpuinfo()
    ctype, hybrid = _core_type(PINNED_CPU)
    fam = ci.get("cpu family")
    mod = ci.get("model")
    step = ci.get("stepping")
    smt = _read("/sys/devices/system/cpu/smt/control")
    no_turbo = _read("/sys/devices/system/cpu/intel_pstate/no_turbo")
    gov = _read(f"/sys/devices/system/cpu/cpu{PINNED_CPU}/cpufreq/scaling_governor")
    return {
        "_comment": ("The x86 acquisition host, captured from this machine by "
                     "bin/host_facts.py so every host fact in the paper is "
                     "regenerable rather than typed."),
        "cpu_model": re.sub(r"\s+", " ", ci.get("model name", "")).replace(
            "(R)", "").replace("(TM)", "").strip() or None,
        "microarch_basis": (f"CPUID family {fam}, model {mod}, stepping {step}"
                            if fam and mod and step else None),
        "cpu_family": int(fam) if fam and fam.isdigit() else None,
        "cpu_model_num": int(mod) if mod and mod.isdigit() else None,
        "cpu_stepping": int(step) if step and step.isdigit() else None,
        "microcode": ci.get("microcode"),
        "hybrid": hybrid,
        "pinned_cpu": PINNED_CPU,
        "pinned_core_type": ctype,
        "doitm": _doitm(PINNED_CPU),
        "smt": smt if smt else None,
        "turbo": ("enabled" if no_turbo == "0" else
                  "disabled" if no_turbo == "1" else "unknown"),
        "governor": gov,
        "kernel": _read("/proc/sys/kernel/osrelease"),
        "machine": "x86_64",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="compare this host against the committed record")
    a = ap.parse_args()
    fresh = capture()
    # microarch is a name, not a machine-readable fact; keep whatever the committed
    # file records rather than inventing one from the model number.
    if OUT.exists():
        old = json.loads(OUT.read_text())
        if old.get("microarch"):
            fresh["microarch"] = old["microarch"]
    if a.check:
        old = json.loads(OUT.read_text()) if OUT.exists() else {}
        drift = {k: (old.get(k), v) for k, v in fresh.items()
                 if k != "_comment" and old.get(k) != v}
        if drift:
            print("host drift against the committed record:")
            for k, (was, now) in sorted(drift.items()):
                print(f"  {k}: committed {was!r} -> this host {now!r}")
            return 1
        print("host matches the committed record")
        return 0
    OUT.write_text(json.dumps(fresh, indent=2) + "\n", encoding="utf-8")
    print(f"host_facts: wrote {OUT}")
    for k in ("cpu_model", "hybrid", "pinned_cpu", "pinned_core_type", "doitm"):
        print(f"  {k:18s} {fresh[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
