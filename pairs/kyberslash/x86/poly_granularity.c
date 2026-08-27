#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <x86intrin.h>
/* The two-class difference at the granularity the attack consumes.

   The per-call design (magnitude_sensitivity.c) asks what one division costs on a
   low against a high operand. An attacker on this leak does not see one division:
   poly_tomsg runs coeff_to_bit over all 256 coefficients of a polynomial, and the
   published attack aggregates over that call. A reviewer asked for the two-class
   difference at THAT granularity, with the effect and the minimum detectable effect
   beside it, so the per-call figure and the attack-relevant figure are both on the
   record and neither is spent as the other.

   Class low: all 256 coefficients drawn from [0, 833), quotient 0. Class high: all
   256 from [1664, 3329), quotient 1 or 2. Each timed region is the real coeff_to_bit
   over one 256-coefficient polynomial, with the division forced to a hardware idiv
   exactly as ks_leak_x86.c forces it, so what is timed is the emitted-division path
   regardless of what the host compiler would choose. Pairs are interleaved with a
   coin flip on the order, as in the sibling programs, so turbo drift and ordering
   cancel. A reciprocal twin of the same region is timed in the same run so the
   ablation exists at this granularity too. */
#define KYBER_Q 3329
#define N 256
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }

static inline uint32_t div_bit(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+KYBER_Q/2), q;
  __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"((uint32_t)KYBER_Q):"eax","edx","cc");
  return q & 1u;
}
static inline uint32_t recip_bit(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+1665u), q;
  __asm__ volatile("movl %1,%%eax\n\t imull %2,%%eax\n\t shrl $28,%%eax\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"(80635u):"eax","cc");
  return q & 1u;
}

static uint64_t timed_poly(const uint16_t *c, int recip){
  uint32_t acc = 0;
  uint64_t t0 = rd();
  if (recip) { for (int i = 0; i < N; i++) acc += recip_bit(c[i]); }
  else       { for (int i = 0; i < N; i++) acc += div_bit(c[i]); }
  uint64_t e = rd();
  return (e - t0) + (acc & 0u);
}

#define PAIRS 400000
int main(void){
  static double diff_div[PAIRS], diff_rec[PAIRS];
  static uint16_t lo[N], hi[N];
  uint32_t rng = 0xC0FFEEu;
  int ns[] = {20000, 100000, 400000};
  for(int i=0;i<2000;i++){ (void)timed_poly(lo,0); (void)timed_poly(hi,0); }
  for(int i=0;i<PAIRS;i++){
    for (int j = 0; j < N; j++) {
      rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
      lo[j] = (uint16_t)(rng % 833);
      hi[j] = (uint16_t)(1664 + (rng % 1665));
    }
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    double a, b, ar, br;
    _mm_lfence();
    if (rng & 1u) { a = (double)timed_poly(lo,0); b = (double)timed_poly(hi,0); }
    else          { b = (double)timed_poly(hi,0); a = (double)timed_poly(lo,0); }
    _mm_lfence();
    if (rng & 2u) { ar = (double)timed_poly(lo,1); br = (double)timed_poly(hi,1); }
    else          { br = (double)timed_poly(hi,1); ar = (double)timed_poly(lo,1); }
    diff_div[i] = b - a;
    diff_rec[i] = br - ar;
  }
  for (int which = 0; which < 2; which++) {
    const double *diff = which ? diff_rec : diff_div;
    const char *tag = which ? "poly_recip" : "poly_div";
    for(int k=0;k<3;k++){
      int n = ns[k];
      double mean=0; for(int i=0;i<n;i++) mean+=diff[i]; mean/=n;
      double var=0; for(int i=0;i<n;i++) var+=(diff[i]-mean)*(diff[i]-mean); var/=(n-1);
      double t = var>0 ? fabs(mean)/sqrt(var/n) : 0.0;
      printf("RESULT %s_n_%d_t %.4f\n", tag, n, t);
      printf("RESULT %s_n_%d_mean_ticks %.6f\n", tag, n, mean);
      printf("RESULT %s_n_%d_mde_ticks %.6f\n", tag, n, 2.80 * sqrt(var / n));
    }
  }
  /* The absolute cost of one polynomial per class, so the difference can be read as a
     fraction of the call the attack sees. */
  double lo_sum = 0, hi_sum = 0; int m = 20000;
  for (int i = 0; i < m; i++) {
    for (int j = 0; j < N; j++) { rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
      lo[j] = (uint16_t)(rng % 833); hi[j] = (uint16_t)(1664 + (rng % 1665)); }
    lo_sum += (double)timed_poly(lo,0); hi_sum += (double)timed_poly(hi,0);
  }
  printf("RESULT poly_div_mean_ticks_low %.3f\n", lo_sum / m);
  printf("RESULT poly_div_mean_ticks_high %.3f\n", hi_sum / m);
  return 0;
}
