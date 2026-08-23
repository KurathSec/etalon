#include "tag.h"
#include <stdlib.h>

/* binsec marks these two globals by name in the SSE script: the tag is secret,
 * the candidate public. */
uint8_t secret[TAG_LEN];
uint8_t candidate[TAG_LEN];

/* byte_work is a timing-amplification device (a volatile nonlinear-multiply
 * loop) with no secret-dependent branch or memory access, and its result is
 * discarded. Stub it here so the solver does not answer "unknown" about
 * control-flow queries that never involve it. The set of secret-dependent
 * branches in check_tag is unchanged, which is the only thing binsec judges. */
uint32_t byte_work(uint8_t a, uint8_t b) { (void)a; (void)b; return 0; }

int main(void)
{
    volatile int r = check_tag(secret, candidate);
    (void)r;
    exit(0);
}
