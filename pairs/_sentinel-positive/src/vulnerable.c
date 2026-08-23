#include "tag.h"

/* VULNERABLE ARM.
 *
 * The loop returns as soon as a byte differs, so the number of iterations, and
 * therefore the running time, is a function of how many leading bytes of the
 * candidate match the secret. That is the leak: a secret-dependent branch whose
 * trip count depends on secret data. */
int check_tag(const uint8_t *secret, const uint8_t *candidate)
{
    for (size_t i = 0; i < TAG_LEN; i++) {
        byte_work(secret[i], candidate[i]);
        if (secret[i] != candidate[i]) {
            return 0;                 /* GROUND TRUTH SITE: early exit on secret data */
        }
    }
    return 1;
}
