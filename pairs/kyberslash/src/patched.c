#include "kyber_slash.h"
/* PATCHED ARM: upstream's fix, verbatim in form.
 *
 * pq-crystals/kyber commit dda29cc63a (2023-12-01, "Updated poly_tomsg to prevent
 * a compiler from using DIV") replaces the division by the constant with
 *     t <<= 1; t += 1665; t *= 80635; t >>= 28;
 * which every target executes in data-independent time. It equals the vulnerable
 * arm's ((2t + KYBER_Q/2) / KYBER_Q) & 1 for every t in [0, KYBER_Q): both are
 * round(2t / q) mod 2, and the two roundings (+1664 with a true division, +1665
 * with the 80635 / 2^28 reciprocal) never straddle a multiple of q on that range.
 * Verified exhaustively over [0, KYBER_Q); the product 8321 * 80635 fits 32 bits.
 *
 * An earlier revision of this arm used a different reciprocal, (d * 315) >> 20 on
 * d = 2t + 1664, which is also exact on the range but is not what upstream ships.
 * The paper's emission map is a claim about specific binaries, so the patched arm
 * is now the shipped form. Different from the vulnerable arm only in that no
 * division instruction is emitted. */
uint16_t coeff_to_bit(uint16_t t)
{
    uint32_t u;
    t += ((int16_t)t >> 15) & KYBER_Q;
    u  = (uint32_t)t;
    u <<= 1;
    u += 1665u;
    u *= 80635u;
    u >>= 28;
    return (uint16_t)(u & 1);
}
