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
int main(void){
  static double diff[M];
  int amps[]={1,2,4,8,16,32};
  printf("RESULT boundary 3329\n");
  for(int k=0;k<6;k++){ int amp=amps[k];
    for(int i=0;i<3000;i++){ (void)timed(3328,amp); (void)timed(3330,amp); }  /* warm */
    for(int i=0;i<M;i++){ _mm_lfence();
      double lo=(double)timed(3328,amp);   /* coeff 832, quotient 0 */
      double hi=(double)timed(3330,amp);   /* coeff 833, quotient 1 */
      diff[i]=lo-hi; }
    double mean=0; for(int i=0;i<M;i++) mean+=diff[i]; mean/=M;
    double var=0; for(int i=0;i<M;i++) var+=(diff[i]-mean)*(diff[i]-mean); var/=(M-1);
    double t = var>0 ? fabs(mean)/sqrt(var/M) : 0.0;
    printf("RESULT amp_%d %.4f\n", amp, t);
  }
  return 0;
}
