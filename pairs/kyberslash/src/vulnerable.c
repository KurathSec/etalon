#include "kyber_slash.h"
/* VULNERABLE ARM: KyberSlash1.
 *
 * Verbatim from pq-crystals/kyber ref/poly.c at
 * a621b8dde405cc507cbcfc5f794570a4f98d69cc (pre-fix). The division by KYBER_Q,
 * which is 3329 and not a power of two, is applied to a secret-dependent value.
 * On a target whose division instruction has data-dependent latency, the
 * decapsulation time leaks the secret coefficient. GROUND-TRUTH SITE. */
uint16_t coeff_to_bit(uint16_t t)
{
    t += ((int16_t)t >> 15) & KYBER_Q;
    t  = (((t << 1) + KYBER_Q/2) / KYBER_Q) & 1;   /* secret-dependent division */
    return t;
}
