# MatrixSSL leak: mechanism recoverability

The nonce-bit-length residual in MatrixSSL's default constant-time `eccMulmodCt`
feeds a recoverable hidden-number-problem. Demonstrated by replacing the noisy
timing column of a 250000-signature 4.2.1 trace with the true nonce ordering (the
private key is used ONLY to order signatures and this is disclosed; it is not a
timing recovery), then running the unchanged vendored Minerva lattice attack:

    recovered: 0837b047cbc9c094d12e5d86dc64811315a2af0019d0f5ffdd357c02e4f24a07

which equals the signing key. So the leak carries enough information to recover the
key; the barrier to end-to-end recovery FROM RAW TIMING on this host is selection
precision, not the mechanism. On this fast out-of-order P-core the fastest 90 of
250000 signatures are ~31% contaminated by full-length nonces timed fast, below what
rank-based Minerva tolerates.

CORRECTED: an earlier revision of this file called that boundary host-conditional and
predicted a quieter core would recover. That excuse does not survive measurement. On
this same host, the AUC between signing time and nonce shortness is 0.63 for MatrixSSL
against 0.80 for libgcrypt, and the fastest 90 signatures are 31% contaminated here
against 3.3% there, so libgcrypt recovers and MatrixSSL does not on identical hardware
(bin/exploit_budget.py). The limit is how much information the leak carries, not how
noisy the host is. The pair is labelled leak-presence certified, recovery pending.

CORRECTED: an earlier revision rested the incomplete-fix finding on the loop bound at
`crypto/pubkey/ecc_math.c:206` (`digidx = get_digit_count(k) - 1`). That cannot produce
the measured effect: a pstm digit is 64 bits on this build, so a 255-bit and a 256-bit
nonce occupy the same four digits and run the identical 256 iterations. The finding
rests instead on the four-design decomposition, which holds the digit count fixed while
varying bit length and locates the residual in the leading-zero phase, whose dummy
double is out of place and so costs three big-integer copies the real one skips:
|t| = 1.4 at equal length, 17.7 at one leading zero, 1197 at sixty-three, and 8371 once
the digit count really differs. The loop bound is a genuine secret-dependent bound but
needs a nonce short by a whole 64-bit digit. Cross-host replicated on aarch64
(87 -> 17, control 1.15). See results/fix_verification.json.
