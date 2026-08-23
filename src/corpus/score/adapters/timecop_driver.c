/* TIMECOP driver: poison the secret, run the entry once under memcheck.
 *
 * The secret is marked undefined via a memcheck client request. Any branch or
 * memory access that depends on it becomes a use of uninitialised value, which
 * memcheck reports. A single execution suffices; this is not a statistical test.
 *
 * The tag-comparison arm is linked in. check_tag branches on the secret in the
 * vulnerable arm and does not in the patched arm, so memcheck flags one and not
 * the other, which is the detection.
 */
#include <valgrind/memcheck.h>
#include <string.h>
#include <stdio.h>
#include "tag.h"

int check_tag(const uint8_t *secret, const uint8_t *candidate);

int main(void) {
  uint8_t secret[TAG_LEN], cand[TAG_LEN];
  memset(secret, 0x41, TAG_LEN);
  memset(cand, 0x41, TAG_LEN);
  cand[TAG_LEN - 1] = 0x42;                 /* differs in the last byte */
  VALGRIND_MAKE_MEM_UNDEFINED(secret, TAG_LEN);   /* poison: secret is the secret */
  volatile int r = check_tag(secret, cand);
  (void)r;
  printf("TIMECOP_DONE\n");
  return 0;
}
