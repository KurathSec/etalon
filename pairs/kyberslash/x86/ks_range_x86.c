#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <x86intrin.h>
/* Latency across the KyberSlash operand range [1664,8320], divisor 3329, and the
   step at dividend=3329 where the quotient crosses 0 -> 1. Turbo cannot be pinned
   without root here, so the step is measured by INTERLEAVED PAIRING: below- and
   above-boundary chains are timed back to back many times and the median paired
   difference is the step, which cancels slow frequency drift that a sequential
   measurement would fold into the signal. The noise floor is the median absolute
   difference between two same-operand measurements, taken the same way. */
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }
#define N 2000000
static uint32_t chain(uint32_t seed,uint32_t d){uint32_t x=seed|1u;
  for(int i=0;i<N;i++){uint32_t q;
    __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                     :"=r"(q):"r"(x),"r"(d):"eax","edx","cc");
    x=q+seed+1u;}
  return x;}
static double one(uint32_t dv){ volatile uint32_t s=0; _mm_lfence();
  uint64_t a=rd(); s+=chain(dv,3329); uint64_t b=rd(); return (double)(b-a)/N; }
static int cmp(const void*x,const void*y){ double d=*(const double*)x-*(const double*)y; return d<0?-1:d>0?1:0; }
static double median(double*v,int n){ qsort(v,n,sizeof(double),cmp); return v[n/2]; }
static double best_of(uint32_t dv,int reps){ double m=1e18; for(int r=0;r<reps;r++){double t=one(dv); if(t<m)m=t;} return m; }
static double tsc_ghz(void){
  struct timespec a,b; uint64_t t0,t1;
  clock_gettime(CLOCK_MONOTONIC,&a); t0=rd();
  struct timespec req={0,200000000L}; nanosleep(&req,NULL);
  t1=rd(); clock_gettime(CLOCK_MONOTONIC,&b);
  double ns=(b.tv_sec-a.tv_sec)*1e9+(b.tv_nsec-a.tv_nsec);
  return (double)(t1-t0)/ns;
}
#define K 41
int main(void){
  printf("RESULT tsc_ghz %.4f\n", tsc_ghz());
  /* wide range for the latency-vs-operand panel (best-of to shed turbo dips) */
  uint32_t divs[]={1,3000,8000,1000000,4000000000u};
  const char* keys[]={"1","3000","8000","1000000","4000000000"};
  for(int s=0;s<5;s++) printf("RESULT lat_dividend_%s %.5f\n",keys[s],best_of(divs[s],9));
  /* paired interleaved step at the boundary: below=3328 (coeff 832, q=0),
     above=3330 (coeff 833, q=1) */
  double dstep[K], dnoise[K];
  for(int k=0;k<K;k++){ double lo=one(3328), hi=one(3330); dstep[k]=hi-lo;
                        double n1=one(3328), n2=one(3328); dnoise[k]=n1>n2?n1-n2:n2-n1; }
  printf("RESULT step_below %.5f\n", best_of(3328,9));
  printf("RESULT step_above %.5f\n", best_of(3330,9));
  printf("RESULT step_ticks %.5f\n", median(dstep,K));
  printf("RESULT noise_floor %.5f\n", median(dnoise,K));
  return 0;
}
