#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <x86intrin.h>
/* Controls for the per-call low-vs-high magnitude test (magnitude_sensitivity.c).
   That test resolves a small per-call difference with the HIGH class faster, which a
   rising operand latency cannot produce, and the paper attributed it to the harness's
   arrangement of the two classes rather than to the divider. A referee asked for the
   measurement that decides it: the same paired design, same timed sequence, same
   randomised order within each pair, with the two classes chosen so that a genuine
   operand dependence and an arrangement artefact predict different readings.
     MODE=same       both calls of a pair divide the SAME operand, drawn from the whole
                     range [0, 3329). Whatever the harness adds to the second call of a
                     pair is what remains; an operand effect cannot appear.
     MODE=lowsplit   both classes inside the low range, quotient 0: [0,416) vs [416,833).
     MODE=highsplit  both classes inside the high range: [1664,2496) vs [2496,3329).
     MODE=lowhigh    the original contrast, [0,833) vs [1664,3329), rerun in the same
                     session so the four figures share one host state.
   Output is one RESULT line per statistic, as magnitude_sensitivity.c prints. */
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
  const char *mode = getenv("MODE"); if (!mode) mode = "same";
  uint32_t rng = 0xC0FFEEu;
  int ns[] = {50000, 200000, 800000, 2000000, 4000000};
  for(int i=0;i<20000;i++){ (void)timed(400); (void)timed(2400); }
  for(int i=0;i<NMAX;i++){
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    uint16_t lo, hi;
    if (!strcmp(mode, "same"))          { lo = hi = (uint16_t)(rng % KYBER_Q); }
    else if (!strcmp(mode, "lowsplit"))  { lo = (uint16_t)(rng % 416);          hi = (uint16_t)(416 + (rng % 417)); }
    else if (!strcmp(mode, "highsplit")) { lo = (uint16_t)(1664 + (rng % 832)); hi = (uint16_t)(2496 + (rng % 833)); }
    else                                 { lo = (uint16_t)(rng % 833);          hi = (uint16_t)(1664 + (rng % 1665)); }
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    double a, b;
    _mm_lfence();
    if (rng & 1u) { a = (double)timed(lo); b = (double)timed(hi); }
    else          { b = (double)timed(hi); a = (double)timed(lo); }
    diff[i] = b - a;                 /* paired: second class minus first class */
  }
  for(int k=0;k<5;k++){
    int n = ns[k];
    double mean=0; for(int i=0;i<n;i++) mean+=diff[i]; mean/=n;
    double var=0; for(int i=0;i<n;i++) var+=(diff[i]-mean)*(diff[i]-mean); var/=(n-1);
    double t = var>0 ? fabs(mean)/sqrt(var/n) : 0.0;
    printf("RESULT n_%d_t %.4f\n", n, t);
    printf("RESULT n_%d_mean_ticks %.6f\n", n, mean);
    printf("RESULT n_%d_mde_ticks %.6f\n", n, 2.80 * sqrt(var / n));
  }
  return 0;
}
