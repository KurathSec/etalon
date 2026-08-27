#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <x86intrin.h>
/* How much budget would a statistical timing test need to resolve the division's
   operand-MAGNITUDE dependence on this x86 host?

   The scored dudect run on this pair uses the conventional fixed-vs-random class
   design and reads the vulnerable arm clean. A batch estimator, however, resolves a
   small end-to-end difference between low-magnitude and high-magnitude coefficients.
   Those are different questions, and quoting one against the other invites the reading
   that the clean verdict is simply wrong. This program answers the sharper question
   directly: run the LOW-vs-HIGH magnitude design, the one the batch estimator uses, as
   a per-call two-class test, and report the budget-invariant tau at increasing n. If
   tau crosses the calibrated null band at some n, the clean verdict is a sensitivity
   floor and this is where it sits; if it does not, the per-call step is below what this
   counter can resolve at any budget we can run.

   Classes are the same as the end-to-end measurement: low = coeff in [0,833) (quotient
   0), high = coeff in [1664,3329) (quotient 1 or 2). Operands are precomputed outside
   the timed region and both classes run the identical timed sequence, so only the
   values fed to the divider differ. Measurements are interleaved in pairs so turbo
   drift cancels within a pair, as in detection_curve.c. */
#define KYBER_Q 3329
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }

static uint64_t timed(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+KYBER_Q/2), q;
  uint64_t t0 = rd();
  __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"((uint32_t)KYBER_Q):"eax","edx","cc");
  uint64_t e = rd();
  return (e - t0) + (q & 0u);
}

#define NMAX 4000000
int main(void){
  static double diff[NMAX];
  uint32_t rng = 0xC0FFEEu;
  int ns[] = {50000, 200000, 800000, 2000000, 4000000};
  /* warm */
  for(int i=0;i<20000;i++){ (void)timed(400); (void)timed(2400); }
  for(int i=0;i<NMAX;i++){
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    uint16_t lo = (uint16_t)(rng % 833);
    uint16_t hi = (uint16_t)(1664 + (rng % 1665));
    /* Randomise which class is timed FIRST within each pair. Timing them in a fixed
       order makes the second call systematically cheaper (warmer predictor and TLB
       state), which shows up as a stable offset of about a tick with the sign of the
       ordering rather than of the operand. The pairing still cancels turbo drift; the
       coin flip cancels the ordering. */
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    double a, b;
    _mm_lfence();
    if (rng & 1u) { a = (double)timed(lo); b = (double)timed(hi); }
    else          { b = (double)timed(hi); a = (double)timed(lo); }
    diff[i] = b - a;                 /* paired: high minus low */
  }
  /* One value per RESULT line: measure.py parses "RESULT <key> <value>". */
  for(int k=0;k<5;k++){
    int n = ns[k];
    double mean=0; for(int i=0;i<n;i++) mean+=diff[i]; mean/=n;
    double var=0; for(int i=0;i<n;i++) var+=(diff[i]-mean)*(diff[i]-mean); var/=(n-1);
    double t = var>0 ? fabs(mean)/sqrt(var/n) : 0.0;
    printf("RESULT n_%d_t %.4f\n", n, t);
    printf("RESULT n_%d_tau %.6f\n", n, t/sqrt((double)n));
    printf("RESULT n_%d_mean_ticks %.6f\n", n, mean);
    /* Minimum detectable effect at alpha 0.05, power 0.8, on this run's spread. */
    printf("RESULT n_%d_mde_ticks %.6f\n", n, 2.80 * sqrt(var / n));
  }
  return 0;
}
