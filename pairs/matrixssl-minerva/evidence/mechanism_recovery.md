# MatrixSSL leak: mechanism recoverability

Status: LEAK-PRESENCE CERTIFIED, RECOVERY PENDING (results/fix_verification.json,
`exploitability`). An earlier revision of this file opened by claiming that the
nonce-bit-length residual in MatrixSSL's default constant-time `eccMulmodCt` feeds a
recoverable hidden-number problem. That claim is withdrawn. The lattice demonstration behind
it replaced the noisy timing column of an uncommitted 250,000-signature trace from the 4.2.1
pre-fix build with the true nonce ordering, using the private key to order the signatures,
then ran the unchanged vendored Minerva lattice attack:

    recovered: 0837b047cbc9c094d12e5d86dc64811315a2af0019d0f5ffdd357c02e4f24a07

which equals the signing key. What that shows is information content: the leak carries
enough information to recover the key once the short nonces are known. It is not a timing
recovery, because the selection an attacker must derive from timing was supplied from the
key, and no recovery from raw timing has succeeded on this pair.

CORRECTED: an earlier revision of this file called the selection barrier host-conditional
and predicted a quieter core would recover. That excuse does not survive measurement. On
this same host, the AUC between signing time and nonce shortness was 0.63 for MatrixSSL
against 0.80 for libgcrypt, and the fastest 90 signatures were 44.4% contaminated by
full-length nonces at a matched 6,000-signature budget and 26.7% at 250,000, against 3.3%
for libgcrypt, so libgcrypt recovers and MatrixSSL does not on identical hardware
(bin/exploit_budget.py). Those MatrixSSL figures came from the uncommitted 4.2.1 trace; on
the committed 25,000-signature 4-3-0 trace the AUC is 0.63 and the contamination of the
fastest 90 is 28.9% (results/exploit_budget_matrixssl.json). The limit is how much
information the leak carries, not how noisy the host is. The pair is labelled leak-presence
certified, recovery pending.

CORRECTED: an earlier revision rested the incomplete-fix finding on the loop bound at
`crypto/pubkey/ecc_math.c:206` (`digidx = get_digit_count(k) - 1`). That cannot produce
the measured effect: a pstm digit is 64 bits on this build, so a 255-bit and a 256-bit
nonce occupy the same four digits and run the identical 256 iterations. The finding
rests instead on the four-design decomposition, which holds the digit count fixed while
varying bit length and locates the residual in the leading-zero phase, whose dummy
double is out of place and so costs three big-integer copies the real one skips. On the
fixed 4-3-0 build, re-acquired on the corrected harness, |t| = 1.7 at equal length, 17 at
one leading zero, 216 at sixty-three, and 219 once the digit count really differs
(results/fix_verification.json, `measurements_full_report.designs`; an earlier revision of
this file printed 1.4, 17.7, 1197 and 8371 from a harness that timed a different curve).
The loop bound is a genuine secret-dependent bound but needs a nonce short by a whole
64-bit digit. An earlier revision also reported a cross-host replication on aarch64; that
run predates the harness correction, so it timed a different curve, and the replication is
withdrawn (`cross_host_replication_RETIRED` in results/fix_verification.json).
