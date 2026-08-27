# KyberSlash on AWS Graviton3 (Neoverse V1)

A platform-bound acquisition on rented aarch64 hosts: first run 2026-08-23 (UTC),
re-run 2026-08-25 on a fresh instance after the harness correction, and it is
that re-run which is recorded in `results/kyberslash_graviton.json`. Like the pair's key
recovery, it cannot be re-derived on the x86 build host; it needs an aarch64
machine. These three programs are the acquisition script, committed so the
measurement is reproducible given the hardware.

- `udiv_lat.c`   sweeps `udiv` latency against dividend magnitude (serial
  dependency chain, so it measures latency not throughput).
- `ks_range.c`   the same over the KyberSlash operand range `[0, 8320]`,
  isolating the step at `dividend = divisor = 3329`.
- `ks_leak.c`    the real `coeff_to_bit` at `-Os`, a two-class fixed-vs-random
  timing test over low and high coefficients.

## How it was run

A `c7g.xlarge` (Graviton3, Neoverse V1, part 0xd40), Ubuntu 26.04, gcc 15.2.0,
the instance's own unpinned host compiler (an earlier revision of this file said
`c7g.4xlarge`; the record, `measure_arm.py` and the acquisition log all say
`c7g.xlarge`). This cell is outside the digest-pinning discipline of the x86-64
build cells: `locks/textprints/` holds its vulnerable-arm disassembly only and
`locks/binaries.lock.json` records no `.text` digest for it.
The instance is virtualized, not `.metal`: `PMCCNTR_EL0` SIGILLs from userspace,
so timing used the virtual counter `cntvct_el0` at 1.05 GHz, averaged over a
dependency chain. That coarse timer was sufficient. A `.metal` instance and a PMU
kernel module were not needed for this measurement.

```
gcc -O2 udiv_lat.c -o u && taskset -c 3 ./u
gcc -O2 ks_range.c -o r && taskset -c 3 ./r
gcc -Os ks_leak.c  -o k && taskset -c 3 ./k
```
