#include "tag.h"

/* NEGATIVE CONTROL, ARM A.
 *
 * Both arms of this pair are the constant-time implementation. Nothing here is
 * a leak, so no analyser may flag it and no key may be recovered from it.
 *
 * Every byte is always visited and the result is accumulated without branching,
 * so the trip count is constant and the running time does not depend on the
 * secret. The work per byte is identical to the vulnerable arm, so the two arms
 * differ in control flow and in nothing else. */
int check_tag(const uint8_t *secret, const uint8_t *candidate)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < TAG_LEN; i++) {
        byte_work(secret[i], candidate[i]);
        diff |= (uint8_t)(secret[i] ^ candidate[i]);
    }
    return (int)((1 & ((diff - 1) >> 8)));
}
