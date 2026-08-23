#include <valgrind/memcheck.h>
#include <string.h>
#include <stdio.h>
#include "reject.h"
int sample_pos(const uint8_t*,size_t,uint32_t*);
int main(void){ uint8_t s[KEY_LEN]; memset(s,50,KEY_LEN);
  VALGRIND_MAKE_MEM_UNDEFINED(s,KEY_LEN); uint32_t rng=0x777;
  volatile int r=sample_pos(s,0,&rng);(void)r; printf("TIMECOP_DONE\n"); return 0;}
