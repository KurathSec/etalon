#include <stdio.h>
#include <stdint.h>
#include <x86intrin.h>
/* Serial 32-bit unsigned div dependency chain on x86-64. Each quotient feeds the
   next dividend, so this measures the div instruction LATENCY, not throughput.
   Divisor fixed at KYBER_Q=3329. Timer is rdtscp: the TSC is invariant (it ticks
   at the nominal base frequency regardless of turbo), so the absolute count is TSC
   ticks rather than core cycles, but the operand dependence we are after is a
   comparison across dividends at one fixed counter rate, exactly as the Graviton
   virtual-counter measurement did. */
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }
#define N 2000000
static uint32_t chain(uint32_t seed, uint32_t divisor){
  uint32_t x = seed | 1u;
  for (int i=0;i<N;i++){
    uint32_t q;
    __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                     : "=r"(q) : "r"(x), "r"(divisor) : "eax","edx","cc");
    x = q + seed + 1u;
  }
  return x;
}
int main(void){
  volatile uint32_t sink=0;
  uint32_t seeds[]={1,50,300,1000,3000,8000,50000,1000000,100000000u,4000000000u};
  for(int s=0;s<10;s++){
    sink+=chain(seeds[s],3329);
    uint64_t best=~0ull;
    for(int rep=0;rep<9;rep++){ _mm_lfence(); uint64_t t0=rd(); sink+=chain(seeds[s],3329); uint64_t t1=rd(); if(t1-t0<best) best=t1-t0; }
    printf("RESULT lat_dividend_%u %.5f\n",seeds[s],(double)best/N);
  }
  return sink==0xdeadbeefu?1:0;
}
