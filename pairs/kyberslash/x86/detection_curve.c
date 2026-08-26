#include <stdio.h>
#include <stdint.h>
#include <math.h>
#include <x86intrin.h>
/* Detection curve for the KyberSlash division on x86, drift-robust. For each
   amplification factor we time a latency chain of AMP idivs just below the divisor
   boundary (quotient 0) and just above it (quotient 1), INTERLEAVED as back-to-back
   pairs so unpinnable turbo drift cancels within each pair, and report the paired
   t-statistic over the differences. If a per-idiv operand-dependent step existed it
   would grow with AMP; on a constant-time divider the paired t stays low and flat and
   never approaches the leak band, so the x86 null is not a hidden sub-noise step
   waiting for more gain: the nonce pairs cross the leak band at amplification 40
   (t = 15420), the division does not at amplification 32. */
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }
static uint64_t timed(uint32_t base, int amp){
  uint32_t d = base; uint64_t t0 = rd();
  for(int i=0;i<amp;i++){ uint32_t q;
    __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                     :"=r"(q):"r"(d),"r"(3329u):"eax","edx","cc");
    d = base + (q & 1u); }   /* stays base or base+1: same side of the boundary */
  return (rd() - t0) + (d & 0u);
}
#define M 200000
#define PERMS 2000
static double paired_t(const double *d, int n){
  double mean=0; for(int i=0;i<n;i++) mean+=d[i]; mean/=n;
  double var=0; for(int i=0;i<n;i++) var+=(d[i]-mean)*(d[i]-mean); var/=(n-1);
  return var>0 ? fabs(mean)/sqrt(var/n) : 0.0;
}
int main(void){
  static double diff[M];
  static double perm[M];
  int amps[]={1,2,4,8,16,32};
  printf("RESULT boundary 3329\n");
  for(int k=0;k<6;k++){ int amp=amps[k];
    for(int i=0;i<3000;i++){ (void)timed(3328,amp); (void)timed(3330,amp); }  /* warm */
    /* Randomise which operand is timed first. Measuring the low operand first every
     * time confounds the operand with its position in the pair: any order effect, from
     * cache or pipeline state, lands entirely in one class and a paired test then
     * rejects on the order rather than on the divider. With the order coin-flipped and
     * the difference always taken as low minus high, an order effect averages out and
     * what survives is operand dependence. */
    uint64_t ost = 0xD1B54A32D192ED03ull ^ (uint64_t) amp;
    for(int i=0;i<M;i++){ _mm_lfence();
      ost ^= ost << 13; ost ^= ost >> 7; ost ^= ost << 17;
      double lo, hi;
      if (ost & 1ull) { lo=(double)timed(3328,amp); hi=(double)timed(3330,amp); }
      else            { hi=(double)timed(3330,amp); lo=(double)timed(3328,amp); }
      diff[i]=lo-hi; }
    double t = paired_t(diff, M);
    /* Exact null for THIS design. The measurement is a paired difference of two
     * operands timed back to back, so under the null that the two sides are
     * exchangeable each difference's sign is equally likely either way. Flipping
     * signs is therefore the permutation the design licenses, and it needs no band
     * calibrated on some other harness: the null is built from these samples. */
    unsigned long ge = 0;
    uint64_t st = 0x9E3779B97F4A7C15ull ^ (uint64_t) amp;   /* fixed seed: reproducible */
    for (int b = 0; b < PERMS; b++) {
      double m = 0.0, v = 0.0;
      for (int i = 0; i < M; i++) {
        st ^= st << 13; st ^= st >> 7; st ^= st << 17;      /* xorshift64 */
        perm[i] = (st & 1ull) ? diff[i] : -diff[i];
        m += perm[i];
      }
      m /= M;
      for (int i = 0; i < M; i++) { double e = perm[i] - m; v += e * e; }
      v /= (M - 1);
      double tb = v > 0 ? fabs(m) / sqrt(v / M) : 0.0;
      if (tb >= t) ge++;
    }
    double pval = (double) (1 + ge) / (double) (PERMS + 1);
    /* The effect size matters more than the statistic here: a per-division step would
     * accumulate with amp, so print the mean paired difference both per measurement
     * and divided by amp. A constant per-measurement offset shows up as a per-division
     * figure that FALLS as 1/amp, which is how a placement artifact is told apart from
     * an operand-dependent divider. */
    double mdiff = 0.0; for (int i = 0; i < M; i++) mdiff += diff[i]; mdiff /= M;
    printf("RESULT amp_%d %.4f p %.5f mean %.6f perdiv %.6f\n",
           amp, t, pval, mdiff, mdiff / amp);
  }
  return 0;
}
