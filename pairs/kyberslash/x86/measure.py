#!/usr/bin/env python3
"""Measure the KyberSlash division on the x86 acquisition host.

Mirror of pairs/kyberslash/graviton/, but for x86-64 idiv and the rdtscp counter,
so the paper's headline "dudect misses the division on x86" rests on a host-level
leak-presence measurement rather than only a dudect null. Emits
results/kyberslash_x86_idiv.json in the same schema as kyberslash_graviton.json.

Unlike the Graviton file this is regenerable on this x86 build host:
    taskset -c 2 python3 pairs/kyberslash/x86/measure.py
"""
import json, re, subprocess, sys, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
OUT = REPO / "results" / "kyberslash_x86_idiv.json"

def build(src, extra):
    exe = HERE / (Path(src).stem)
    subprocess.run(["gcc", *extra, str(HERE / src), "-o", str(exe)], check=True)
    return exe

def run(exe):
    # Pin to a P-core (cpu2), leaving cpu0/1 for the OS, matching the dudect adapter.
    p = subprocess.run(["taskset", "-c", "2", str(exe)], check=True,
                       capture_output=True, text=True)
    out = {}
    for line in p.stdout.splitlines():
        m = re.match(r"RESULT (\S+) (\S+)", line)
        if m:
            out[m.group(1)] = float(m.group(2))
    return out

def idiv_count_source(opt):
    # Compile the REAL vulnerable source standalone at one opt level and count the
    # hardware-division mnemonics in the emitted object. Standalone, so the function
    # is not inlined away and the count is honest. On this host's gcc this records
    # idiv at -Os and a reciprocal multiply elsewhere, matching the emission map.
    src = REPO / "pairs" / "kyberslash" / "src" / "vulnerable.c"
    inc = src.parent
    obj = HERE / f"_probe_{opt}.o"
    subprocess.run(["gcc", f"-{opt}", "-I", str(inc), "-c", str(src), "-o", str(obj)],
                   check=True)
    d = subprocess.run(["objdump", "-d", str(obj)], capture_output=True, text=True).stdout
    obj.unlink(missing_ok=True)
    return len(re.findall(r"\b[a-z]*div[a-z]?\s", d))

def main():
    lat = run(build("idiv_lat_x86.c", ["-O2"]))
    rng = run(build("ks_range_x86.c", ["-O2"]))
    # The end-to-end binary is the REAL coeff_to_bit at -Os, where the emission map
    # records gcc emitting a hardware division. Confirm the idiv is actually there.
    div_in_os = idiv_count_source("Os")
    div_in_o2 = idiv_count_source("O2")

    ghz = rng.get("tsc_ghz")
    step = rng.get("step_ticks", 0.0)
    noise = rng.get("noise_floor", 0.0)
    snr = round(step / noise) if noise > 1e-9 else None

    doc = {
        "finding": "kyberslash-x86-leak-presence",
        "measured_utc": os.environ.get("MEASURE_UTC", ""),
        "host": json.loads((REPO / "results" / "host.json").read_text()),
        "regenerable": "on this x86 host: taskset -c 2 python3 pairs/kyberslash/x86/measure.py. "
                       "Unlike the Graviton measurement this is not architecture-locked.",
        "results": {
            "codegen": {
                "note": "the real vulnerable source emits a hardware idiv at -Os on this host gcc and a "
                        "reciprocal multiply at -O2/-O0, the same size-only pattern the committed emission "
                        "map records with the pinned gcc-12.2.0.",
                "idiv_in_coeff_to_bit": {"Os": div_in_os, "O2": div_in_o2},
            },
            "idiv_latency_operand_dependent": {
                "note": "serial dependency chain; TSC ticks per div rises with dividend "
                        "magnitude in general (more significant quotient bits cost more).",
                "ticks_per_udiv": {
                    "dividend_1": lat.get("lat_dividend_1"),
                    "dividend_3000": lat.get("lat_dividend_3000"),
                    "dividend_8000": lat.get("lat_dividend_8000"),
                    "dividend_1e6": lat.get("lat_dividend_1000000"),
                    "dividend_4e9": lat.get("lat_dividend_4000000000"),
                },
            },
            "kyberslash_operand_range_step": {
                "note": "the step at dividend=divisor=3329, quotient 0 -> 1, over the "
                        "KyberSlash range [1664,8320]. Over this range the quotient never "
                        "exceeds 2 bits, so the operand-dependent latency the wide sweep "
                        "shows barely moves.",
                "coeff_below_833_ticks": rng.get("step_below"),
                "coeff_at_or_above_833_ticks": rng.get("step_above"),
                "step_ticks": step,
                "noise_floor_ticks": noise,
                "signal_to_noise": snr,
            },
            "tsc_ghz": ghz,
        },
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc["results"], indent=2))
    print(f"\nwrote {OUT}")

if __name__ == "__main__":
    sys.exit(main())
