/* varlat driver for KyberSlash's coeff_to_bit.
 *
 * Poison the secret coefficient, enable TIMECOP mode, run coeff_to_bit. The
 * patched Valgrind reports a "Variable-latency instruction operand" when the
 * secret-dependent idiv executes on the poisoned value. This detects the leak at
 * the instruction level, so it fires on x86 even though this CPU's divider does
 * not leak enough measured time for a statistical test to catch.
 */
#include <valgrind/memcheck.h>
#include <string.h>
#include <stdio.h>
#include "kyber_slash.h"

uint16_t coeff_to_bit(uint16_t t);

int main(void) {
  uint16_t v = 1234;
  VALGRIND_MAKE_MEM_UNDEFINED(&v, sizeof(v));   /* the coefficient is the secret */
  VALGRIND_ENABLE_TIMECOP_MODE;                 /* turn on variable-latency checks */
  volatile uint16_t r = coeff_to_bit(v);
  (void)r;
  printf("VARLAT_DONE\n");
  return 0;
}
