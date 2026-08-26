/* Emission in context, not in isolation.
 *
 * The emission map is measured on coeff_to_bit compiled as its own function. A
 * reviewer's objection: after inlining into the loop that actually calls it, the
 * compiler sees the caller's range information and may lower the division
 * differently, so the isolated measurement could be reporting a cell the shipped
 * build never has. This file is the same arm placed in that context, so the two can
 * be compared in the same build cell.
 *
 * The caller is the shape the reference implementation uses: a loop over
 * KYBER_N coefficients of a polynomial packing one bit each into a message byte,
 * which is where the pre-fix reference applied this division. The function under
 * test keeps its source unchanged; only its surroundings differ.
 *
 * ARM is selected at compile time: -DARM_VULNERABLE or -DARM_PATCHED, so both arms
 * pass through the identical caller and any difference is the arm.
 */
#include "kyber_slash.h"
#include <stdint.h>

#define KYBER_N 256

#if defined(ARM_PATCHED)
/* patched.c's body, inlined here verbatim: multiply-shift, exact on [0, 8321). */
static inline uint16_t coeff_to_bit_ctx(uint16_t t)
{
    uint32_t d;
    t += ((int16_t) t >> 15) & KYBER_Q;
    d  = (uint32_t) ((t << 1) + KYBER_Q / 2);
    d  = (d * 315u) >> 20;
    return (uint16_t) (d & 1);
}
#else
/* vulnerable.c's body, inlined here verbatim: the secret-dependent division. */
static inline uint16_t coeff_to_bit_ctx(uint16_t t)
{
    t += ((int16_t) t >> 15) & KYBER_Q;
    t  = (((t << 1) + KYBER_Q / 2) / KYBER_Q) & 1;
    return t;
}
#endif

/* The caller: pack one bit per coefficient, as the reference does at this site. */
void poly_tomsg_ctx(uint8_t msg[KYBER_N / 8], const int16_t a[KYBER_N])
{
    for (unsigned i = 0; i < KYBER_N / 8; i++) {
        msg[i] = 0;
        for (unsigned j = 0; j < 8; j++) {
            uint16_t t = coeff_to_bit_ctx((uint16_t) a[8 * i + j]);
            msg[i] |= (uint8_t) (t << j);
        }
    }
}
