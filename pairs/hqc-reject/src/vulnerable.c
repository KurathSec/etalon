#include "reject.h"
/* Amplification, overridable at build time with -DAMP=n for the registered
 * detection curve. The default is the committed value, so an unparameterised
 * build of this file is exactly what it was. */
#ifndef AMP
#define AMP 200
#endif
/* VULNERABLE ARM: HQC/BIKE-style secret-dependent rejection sampling.
 *
 * Draws pseudo-random bytes and accepts the first with value < the secret
 * threshold for this position. The number of draws is geometrically
 * distributed with mean 256/secret[pos], so the running time leaks the secret
 * byte. This is the rejection-sampling timing leak (Don't Reject This, TCHES
 * 2022; the HQC CVE-2025-52473 family). GROUND-TRUTH SITE. */
static uint32_t xorshift(uint32_t *s){ uint32_t x=*s; x^=x<<13; x^=x>>17; x^=x<<5; return *s=x; }
int sample_pos(const uint8_t *secret, size_t pos, uint32_t *rng){
  uint8_t thr = secret[pos] | 1;          /* avoid zero threshold */
  int draws = 0;
  for(;;){
    draws++;
    uint8_t b = (uint8_t)(xorshift(rng) & 0xff);
    volatile uint32_t work=0; for(int j=0;j<AMP;j++) work+=xorshift(rng); (void)work;
    if (b < thr) return draws;             /* SECRET-DEPENDENT loop count */
  }
}
