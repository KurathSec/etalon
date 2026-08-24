#ifndef TAG_H
#define TAG_H
#include <stddef.h>
#include <stdint.h>

#define TAG_LEN 16

/* Returns 1 if the candidate tag equals the secret HMAC tag, 0 otherwise.
 *
 * This is the comparison OpenVPN's openvpn_decrypt performed on the received
 * HMAC (CVE-2013-2061). The two arms of this pair differ only in the body of
 * this function: the vulnerable arm returns on the first mismatched byte, the
 * patched arm compares in constant time. TAG_LEN is a representative truncated
 * tag length; the mechanism is the byte-by-byte early return, not the width. */
int check_tag(const uint8_t *secret, const uint8_t *candidate);

/* Work proportional to one byte comparison.
 *
 * A single memcmp of one tag byte differs between the arms by only a couple of
 * cycles, which is below the noise floor of a machine with three core frequency
 * tiers and no way to disable turbo without root. So each byte costs a fixed,
 * visible amount of work, amplifying an existing signal rather than creating
 * one, so that the byte-by-byte forgery is deterministic from the committed
 * timings. The amplification is recorded as a divergence in pair.toml. */
uint32_t byte_work(uint8_t a, uint8_t b);

#endif
