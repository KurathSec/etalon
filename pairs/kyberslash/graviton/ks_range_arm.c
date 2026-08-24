#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
/* Latency across the KyberSlash operand range on aarch64, and the step at the
   divisor boundary, measured the same robust way as the x86 harness: below- and
   above-boundary chains are timed back to back K times and the median paired
   difference is the step, cancelling frequency drift; the noise floor is the
   median absolute difference between two same-operand measurements. This makes
   noise_floor a value a committed program derives, not a hand-entered constant. */
static inline uint64_t cvt(void){uint64_t c;__asm__ volatile("mrs %0,cntvct_el0":"=r"(c));return c;}
static inline uint64_t cfrq(void){uint64_t c;__asm__ volatile("mrs %0,cntfrq_el0":"=r"(c));return c;}
#define N 2000000
static uint32_t chain(uint32_t seed,uint32_t d){uint32_t x=seed|1u;
  for(int i=0;i<N;i++){uint32_t q;__asm__ volatile("udiv %w0,%w1,%w2":"=r"(q):"r"(x),"r"(d));x=q+seed+1u;}
  return x;}
static double one(uint32_t dv){ volatile uint32_t s=0;
  uint64_t a=cvt(); s+=chain(dv,3329); uint64_t b=cvt(); return (double)(b-a)/N; }
static int cmp(const void*x,const void*y){ double d=*(const double*)x-*(const double*)y; return d<0?-1:d>0?1:0; }
static double median(double*v,int n){ qsort(v,n,sizeof(double),cmp); return v[n/2]; }
static double best_of(uint32_t dv,int reps){ double m=1e18; for(int r=0;r<reps;r++){double t=one(dv); if(t<m)m=t;} return m; }
#define K 201
int main(void){
  printf("RESULT counter_ghz %.4f\n",(double)cfrq()/1e9);
  uint32_t divs[]={1,3000,8000,1000000,4000000000u};
  const char* keys[]={"1","3000","8000","1000000","4000000000"};
  for(int s=0;s<5;s++) printf("RESULT lat_dividend_%s %.5f\n",keys[s],best_of(divs[s],9));
  /* paired interleaved step: below=3328 (coeff 832, q=0), above=3330 (coeff 833, q=1) */
  double dstep[K], dnoise[K];
  for(int k=0;k<K;k++){ double lo=one(3328), hi=one(3330); dstep[k]=hi-lo;
                        double n1=one(3328), n2=one(3328); dnoise[k]=n1>n2?n1-n2:n2-n1; }
  printf("RESULT step_below %.5f\n", best_of(3328,9));
  printf("RESULT step_above %.5f\n", best_of(3330,9));
  printf("RESULT step_ticks %.5f\n", median(dstep,K));
  printf("RESULT noise_floor %.5f\n", median(dnoise,K));
  /* dump the paired step samples for a bootstrap CI downstream */
  FILE* f=fopen("/tmp/arm_dstep.txt","w"); for(int k=0;k<K;k++) fprintf(f,"%.6f\n",dstep[k]); fclose(f);
  return 0;
}
