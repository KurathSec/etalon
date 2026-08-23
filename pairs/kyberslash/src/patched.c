#include "kyber_slash.h"
/* PATCHED ARM.
 *
 * The upstream fix replaces the division by a constant by a multiply-and-shift,
 * which every target executes in data-independent time. The reciprocal
 * (d * 315) >> 20 equals d / KYBER_Q exactly for every dividend this function
 * can produce: after the conditional add, t is in [0, KYBER_Q), so the dividend
 * (t << 1) + KYBER_Q/2 is at most 8320, and the constant is exact on [0, 8321).
 * Verified exhaustively over the input range. Different from the vulnerable arm
 * only in that no division instruction is emitted. */
uint16_t coeff_to_bit(uint16_t t)
{
    uint32_t d;
    t += ((int16_t)t >> 15) & KYBER_Q;
    d  = (uint32_t)((t << 1) + KYBER_Q/2);
    d  = (d * 315u) >> 20;              /* exact floor(d / KYBER_Q) for d < 8321 */
    return (uint16_t)(d & 1);
}
