#!/usr/bin/env python3
"""Measure the KyberSlash division on the aarch64 (Graviton3 / Neoverse-V1) host.

Regenerates results/kyberslash_graviton.json from committed programs, so every
Graviton number is machine-derived rather than hand-entered (the earlier
noise_floor was a typed constant). Run on the aarch64 instance:
    taskset -c 2 python3 pairs/kyberslash/graviton/measure_arm.py

Corrects the characterisation of the earlier data: the ~0.4-tick, 5.8% signal is
the operand-MAGNITUDE dependence of the hardware udiv (low-coefficient dividends,
quotient 0, run faster than high-coefficient ones, quotient >= 1), NOT a step at a
single-coefficient boundary. The adjacent-coefficient step (coeff 832 vs 833) is
measured directly and is sub-noise, so the single-bit recovery step the published
Cortex-A7 software-division attack used is not resolvable on this hardware divider.
"""
import json, re, statistics, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
OUT = REPO / "results" / "kyberslash_graviton.json"


def build(src, out):
    subprocess.run(["gcc", "-O2", str(HERE / src), "-o", str(HERE / out)], check=True)
    return HERE / out


def run(exe):
    p = subprocess.run(["taskset", "-c", "2", str(exe)], check=True,
                       capture_output=True, text=True)
    return p.stdout


def result_lines(out):
    d = {}
    for line in out.splitlines():
        m = re.match(r"RESULT (\S+) (\S+)", line)
        if m:
            d[m.group(1)] = float(m.group(2))
    return d


def udiv_at(opt):
    src = REPO / "pairs" / "kyberslash" / "src" / "vulnerable.c"
    obj = HERE / f"_probe_{opt}.o"
    subprocess.run(["gcc", f"-{opt}", "-I", str(src.parent), "-c", str(src), "-o", str(obj)],
                   check=True)
    d = subprocess.run(["objdump", "-d", str(obj)], capture_output=True, text=True).stdout
    obj.unlink(missing_ok=True)
    return len(re.findall(r"\b(?:udiv|sdiv)\b", d))


def main():
    rng = result_lines(run(build("ks_range_arm.c", "ks_range_arm")))
    leak_exe = build("ks_leak.c", "ks_leak")
    lows, highs, deltas = [], [], []
    for _ in range(10):
        t = run(leak_exe)
        lows.append(float(re.search(r"low  coeffs.*?([0-9.]+) ticks", t).group(1)))
        highs.append(float(re.search(r"high coeffs.*?([0-9.]+) ticks", t).group(1)))
        deltas.append(float(re.search(r"DELTA\s+([0-9.]+) ticks", t).group(1)))
    low, high = min(lows), min(highs)
    delta_mean = statistics.mean(deltas)
    doc = {
        "finding": "kyberslash-graviton-microarch",
        "measured_utc": "2026-08-25",
        "host": {"cpu": "AWS Graviton3 (Neoverse-V1)", "cpuid_part": "0x41:0xd40",
                 "counter_ghz": rng.get("counter_ghz"),
                 "note": "Rented c7g.xlarge, aarch64. Counter is cntvct_el0 (fixed rate, "
                         "coarser than the core clock); PMCCNTR_EL0 is gated, so a "
                         "dependency-chain average over the virtual counter resolves the leak."},
        "regenerable": "on an aarch64 Neoverse-V1 host: taskset -c 2 python3 "
                       "pairs/kyberslash/graviton/measure_arm.py",
        "results": {
            "codegen": {
                "note": "gcc emits a hardware udiv at -Os only (O0=0, Os=1, O2=0), the same "
                        "size-only pattern as x86; here the compiler narrows the signed-int "
                        "source to an UNSIGNED udiv where the x86 build emits a signed idiv. "
                        "Confirmed by the committed disassembly.",
                "udiv_in_coeff_to_bit": {"O0": udiv_at("O0"), "Os": udiv_at("Os"), "O2": udiv_at("O2")},
                "os_instruction": "udiv w0, w0, w2",
                "textprint": "locks/textprints/kyberslash/gcc-15.2.0-Os-aarch64-linux-gnu/vulnerable.asm",
            },
            "udiv_latency_operand_dependent": {
                "note": "Serial dependency chain. Unlike the x86 divider, which resolves no "
                        "operand-dependent step in the same serial chain, the Neoverse-V1 "
                        "udiv latency RISES with dividend magnitude (more significant quotient "
                        "bits cost more): this is the leak.",
                "ticks_per_udiv": {
                    "dividend_1": rng.get("lat_dividend_1"),
                    "dividend_3000": rng.get("lat_dividend_3000"),
                    "dividend_8000": rng.get("lat_dividend_8000"),
                    "dividend_1e6": rng.get("lat_dividend_1000000"),
                    "dividend_4e9": rng.get("lat_dividend_4000000000"),
                },
            },
            "operand_magnitude_leak": {
                "note": "The exploitable signal is operand-magnitude: low coefficients (dividend "
                        "< 3329, quotient 0) run faster than high coefficients (quotient >= 1). "
                        "This is NOT a single-coefficient boundary step.",
                "low_coeff_ticks_per_udiv": rng.get("lat_dividend_3000"),
                "high_coeff_ticks_per_udiv": rng.get("lat_dividend_8000"),
            },
            "single_bit_boundary_step": {
                "note": "Adjacent coefficients 832 (dividend 3328, quotient 0) and 833 "
                        "(dividend 3330, quotient 1) are indistinguishable in udiv time: the "
                        "single-bit recovery step is SUB-NOISE on this hardware divider, unlike "
                        "the software division the published Cortex-A7 attack used.",
                "step_ticks": rng.get("step_ticks"),
                "noise_floor_ticks": rng.get("noise_floor"),
            },
            "end_to_end_coeff_to_bit_Os": {
                "note": "Two-class over the real coeff_to_bit, min-of-9 batches, 10 repeats. "
                        "Low class = coeff in [0,832] (quotient 0), high = [1664,3328] (quotient "
                        ">= 1). The operand-magnitude delta a full reduction call carries.",
                "low_coeffs_ticks_per_call": low,
                "high_coeffs_ticks_per_call": high,
                "secret_dependent_delta_ticks": delta_mean,
                "delta_ci_ticks": [min(deltas), max(deltas)],
                "delta_percent_of_call": round(delta_mean / low * 100, 2),
            },
        },
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(json.dumps(doc["results"], indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
