#ifndef TAG_H
#define TAG_H
#include <stddef.h>
#include <stdint.h>

#define TAG_LEN 16

/* check_tag runs a certified constant-time field operation over the secret and
 * candidate. It is not a comparison; the name matches the shared driver interface
 * so the existing dudect, timecop, varlat and binsec drivers score it unchanged.
 * The two arms are identical: this is a certified-CT negative, so there is no
 * vulnerable body, and any analyser that flags it is a genuine false positive. */
int check_tag(const uint8_t *secret, const uint8_t *candidate);

/* Some drivers reference byte_work; the certified negative does not amplify, so it
 * is a no-op here, present only to satisfy the shared driver interface. */
uint32_t byte_work(uint8_t a, uint8_t b);

#endif
