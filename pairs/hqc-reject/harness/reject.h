#ifndef REJECT_H
#define REJECT_H
#include <stdint.h>
#include <stddef.h>
#define KEY_LEN 8
/* Rejection-sample one output byte using a secret per-position threshold.
 * The two arms differ only in this function. Returns the number of draws taken
 * (the leak in the vulnerable arm; constant in the patched arm). */
int sample_pos(const uint8_t *secret, size_t pos, uint32_t *rng_state);
#endif
