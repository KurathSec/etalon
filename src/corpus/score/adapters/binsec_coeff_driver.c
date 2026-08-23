/* binsec driver for KyberSlash's coeff_to_bit.
 *
 * The secret coefficient is a named global, marked secret in the SSE script. The
 * division by the constant KYBER_Q has a secret-dependent dividend, which the
 * checkct dividend feature reports as a variable-latency leak, symbolically and
 * without measuring time. The patched arm's multiply-shift emits no division. */
#include "kyber_slash.h"
#include <stdlib.h>
uint16_t secret;
int main(void) { volatile uint16_t r = coeff_to_bit(secret); (void)r; exit(0); }
