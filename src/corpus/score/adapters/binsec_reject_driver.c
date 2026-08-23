/* binsec driver for the HQC/BIKE rejection-sampling leak.
 *
 * The secret threshold bytes are a named global, marked secret. The RNG seed is
 * concrete, so the accept test `b < thr` branches on secret data: a
 * secret-dependent control-flow leak binsec reports on the vulnerable arm. The
 * reject loop is unbounded, so exploration is incomplete by construction; the
 * leak is nonetheless found, and an incomplete-but-secure patched arm is
 * INCONCLUSIVE, never silently clean. */
#include "reject.h"
#include <stdlib.h>
uint8_t secret[8];
int main(void) { uint32_t rng = 12345u; volatile int r = sample_pos(secret, 0, &rng); (void)r; exit(0); }
