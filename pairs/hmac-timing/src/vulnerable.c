#include "tag.h"

/* VULNERABLE ARM. Reproduces OpenVPN openvpn_decrypt's HMAC comparison
 * (CVE-2013-2061).
 *
 * The loop returns as soon as a byte differs, so the number of iterations, and
 * therefore the running time, reveals how many leading bytes of a forged tag are
 * correct. An attacker forges a valid tag one byte at a time from the timing,
 * bypassing authentication. GROUND-TRUTH SITE: early exit on secret data. */
int check_tag(const uint8_t *secret, const uint8_t *candidate)
{
    for (size_t i = 0; i < TAG_LEN; i++) {
        byte_work(secret[i], candidate[i]);
        if (secret[i] != candidate[i]) {
            return 0;                 /* GROUND TRUTH SITE: early exit on secret data */
        }
    }
    return 1;
}
