#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <x86intrin.h>
#define KYBER_Q 3329
/* The real KyberSlash coeff_to_bit, with the division FORCED to a hardware idiv via
   inline asm. The host gcc 16.1.1 already emits the idiv at -Os (only), matching the
   pinned gcc-12.2.0 in the emission map; forcing it here makes the measurement
   compiler-independent and holds the idiv fixed regardless of the -O level used to
   build this file. The measured operand is a signed int in coeff_to_bit; divl is used
   in the forcing asm only to time the shared 32-bit integer divider (idiv and divl
   share the unit and are latency-equivalent for these non-negative operands). */
static uint16_t coeff_to_bit(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+KYBER_Q/2), q;
  __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"((uint32_t)KYBER_Q):"eax","edx","cc");
  return (uint16_t)(q & 1);
}
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }
#define M 4000000

/* Operands are generated OUTSIDE the timed region and the two classes are timed by
   the SAME loop over a precomputed array. An earlier revision generated each class
   inside the timed loop with a different expression, `rng%833` for the low class
   against `1664+(rng%1665)` for the high one, and seeded the two classes differently.
   Those are two different compile-time constant reductions, each lowered to its own
   multiply-shift sequence, so the measured difference conflated the divider's operand
   dependence with the cost of the surrounding operand generation. Here both classes
   execute identical instructions and differ only in the values fed to the divider,
   which is what the measurement claims to isolate. */
static uint16_t *make_class(int hi, uint32_t seed){
  uint16_t *v = malloc((size_t)M * sizeof *v);
  uint32_t rng = seed;
  for (int i = 0; i < M; i++){
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    v[i] = hi ? (uint16_t)(1664 + (rng % 1665)) : (uint16_t)(rng % 833);
  }
  return v;
}
static uint64_t batch(const uint16_t *v){
  volatile uint16_t sink=0;
  _mm_lfence(); uint64_t t0=rd();
  for(int i=0;i<M;i++) sink += coeff_to_bit(v[i]);
  return rd()-t0;
}
int main(void){
  /* Same seed for both classes: the class differs in operand magnitude only, not in
     the random trajectory. */
  uint16_t *lov = make_class(0, 0xA), *hiv = make_class(1, 0xA);
  batch(lov); batch(hiv);                      /* warm */
  uint64_t lo=~0ull, hi=~0ull;
  for(int r=0;r<11;r++){uint64_t a=batch(lov),b=batch(hiv); if(a<lo)lo=a; if(b<hi)hi=b;}
  double lp=(double)lo/M, hp=(double)hi/M;
  printf("RESULT e2e_low %.5f\n",lp);
  printf("RESULT e2e_high %.5f\n",hp);
  printf("RESULT e2e_delta %.5f\n",hp-lp);
  printf("RESULT e2e_pct %.4f\n",(hp-lp)/lp*100.0);
  free(lov); free(hiv);
  return 0;
}
