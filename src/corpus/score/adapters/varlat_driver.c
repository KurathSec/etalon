/* varlat driver for the tag-comparison sentinels. Poison the secret, enable
 * TIMECOP mode, run check_tag. The vulnerable arm branches on the secret (an
 * uninitialised-value condition); the patched arm does not. */
#include <valgrind/memcheck.h>
#include <string.h>
#include <stdio.h>
#include "tag.h"
int check_tag(const uint8_t *secret, const uint8_t *candidate);
int main(void) {
  uint8_t secret[TAG_LEN], cand[TAG_LEN];
  memset(secret, 0x41, TAG_LEN); memset(cand, 0x41, TAG_LEN);
  cand[TAG_LEN-1] = 0x42;
  VALGRIND_MAKE_MEM_UNDEFINED(secret, TAG_LEN);
  VALGRIND_ENABLE_TIMECOP_MODE;
  volatile int r = check_tag(secret, cand); (void)r;
  printf("VARLAT_DONE\n");
  return 0;
}
