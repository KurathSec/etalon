#ifndef TAG_H
#define TAG_H
#include <stddef.h>
#include <stdint.h>

#define TAG_LEN 16

/* Returns 1 if the candidate equals the secret tag, 0 otherwise.
 *
 * The two arms of this pair differ only in the body of this function. */
int check_tag(const uint8_t *secret, const uint8_t *candidate);

/* Work proportional to one byte comparison.
 *
 * This exists so the sentinel is unambiguous. A real early-exit comparison
 * leaks one or two cycles per byte, which is below the noise floor of a machine
 * with three core frequency tiers and no way to disable turbo without root. A
 * control that only fires on a quiet machine is not a control. So each byte
 * costs a fixed, visible amount of work, and the resulting signal is large
 * enough that recovery is deterministic rather than statistical.
 *
 * This is why the pair is marked synthetic and can never enter a recall
 * denominator: the mechanism is real, a secret-dependent branch, but the
 * magnitude is manufactured. */
uint32_t byte_work(uint8_t a, uint8_t b);

#endif
