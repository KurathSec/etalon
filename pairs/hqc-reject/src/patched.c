#include "reject.h"
/* Amplification, overridable at build time with -DAMP=n for the registered
 * detection curve. The default is the committed value, so an unparameterised
 * build of this file is exactly what it was. */
#ifndef AMP
#define AMP 200
#endif
/* PATCHED ARM: constant-time rejection sampling.
 *
 * Always performs a fixed number of draws and selects obliviously, so the draw
 * count and running time do not depend on the secret. Same distribution of
 * accepted values in expectation; no timing leak. */
static uint32_t xorshift(uint32_t *s){ uint32_t x=*s; x^=x<<13; x^=x>>17; x^=x<<5; return *s=x; }
int sample_pos(const uint8_t *secret, size_t pos, uint32_t *rng){
  uint8_t thr = secret[pos] | 1;
  int found = 0; volatile int sink = 0;
  for (int i = 0; i < 512; i++){           /* CONSTANT loop count */
    uint8_t b = (uint8_t)(xorshift(rng) & 0xff);
    volatile uint32_t work=0; for(int j=0;j<AMP;j++) work+=xorshift(rng); (void)work;
    int hit = (b < thr) & !found;
    found |= hit; sink += hit;             /* oblivious: no early exit */
  }
  (void)sink;
  return 512;
}
