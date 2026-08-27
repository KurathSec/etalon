#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <x86intrin.h>
/* The ABLATION for magnitude_sensitivity.c.

   That program times a hardware idiv on low-magnitude against high-magnitude
   operands, per call, paired and interleaved, and resolves a small effect on this
   host (about 0.73 ticks at four million pairs). A reviewer asked the question that
   decides what that effect is: does it belong to the DIVIDER, or to everything
   around it (the pair ordering, the operand preparation, the counter itself)? The
   answer is an ablation, and this is it: the identical harness, the identical two
   classes, the identical timed sequence, with the division replaced by the
   reciprocal multiply-and-shift the upstream fix uses (t <<= 1; t += 1665;
   t *= 80635; t >>= 28, pq-crystals/kyber commit dda29cc). If the effect
   persists here, it is in the surroundings and the divider is not shown to carry
   it; if it disappears, it belongs to the divider and "flat" is withdrawn.

   The multiply is forced through inline asm exactly as the idiv is in the sibling
   program, so the compiler cannot hoist or fold the timed operation. The product
   fits 32 bits: the largest operand is 2 * 3328 + 1665 = 8321, and
   8321 * 80635 < 2^32. */
#define KYBER_Q 3329
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }

static uint64_t timed(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+1665u), q;
  uint64_t t0 = rd();
  __asm__ volatile("movl %1,%%eax\n\t imull %2,%%eax\n\t shrl $28,%%eax\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"(80635u):"eax","cc");
  uint64_t e = rd();
  return (e - t0) + (q & 0u);
}

#define NMAX 4000000
int main(void){
  static double diff[NMAX];
  uint32_t rng = 0xC0FFEEu;
  int ns[] = {50000, 200000, 800000, 2000000, 4000000};
  for(int i=0;i<20000;i++){ (void)timed(400); (void)timed(2400); }
  for(int i=0;i<NMAX;i++){
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    uint16_t lo = (uint16_t)(rng % 833);
    uint16_t hi = (uint16_t)(1664 + (rng % 1665));
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    double a, b;
    _mm_lfence();
    if (rng & 1u) { a = (double)timed(lo); b = (double)timed(hi); }
    else          { b = (double)timed(hi); a = (double)timed(lo); }
    diff[i] = b - a;
  }
  for(int k=0;k<5;k++){
    int n = ns[k];
    double mean=0; for(int i=0;i<n;i++) mean+=diff[i]; mean/=n;
    double var=0; for(int i=0;i<n;i++) var+=(diff[i]-mean)*(diff[i]-mean); var/=(n-1);
    double t = var>0 ? fabs(mean)/sqrt(var/n) : 0.0;
    printf("RESULT recip_n_%d_t %.4f\n", n, t);
    printf("RESULT recip_n_%d_tau %.6f\n", n, t/sqrt((double)n));
    printf("RESULT recip_n_%d_mean_ticks %.6f\n", n, mean);
    /* The minimum detectable effect at alpha 0.05 and power 0.8 on this run's own
       spread: (1.96 + 0.84) * sd / sqrt(n). Reported beside the mean so a reader
       can see whether a null here is a null or a floor. */
    printf("RESULT recip_n_%d_mde_ticks %.6f\n", n, 2.80 * sqrt(var / n));
  }
  return 0;
}
