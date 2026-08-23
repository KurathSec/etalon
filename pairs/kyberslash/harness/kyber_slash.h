#ifndef KYBER_SLASH_H
#define KYBER_SLASH_H
#include <stdint.h>
#define KYBER_Q 3329
/* Reduce one secret-dependent coefficient to one message bit.
 *
 * This is the inner step of poly_tomsg from the Kyber reference implementation
 * at the pinned commit. The two arms differ only in this function. */
uint16_t coeff_to_bit(uint16_t t);
#endif
