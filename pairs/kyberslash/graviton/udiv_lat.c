#include <stdio.h>
#include <stdint.h>
/* Serial udiv dependency chain: each divide feeds the next, so we measure
   LATENCY, not throughput. Divisor fixed at KYBER_Q=3329. */
static inline uint64_t cvt(void){uint64_t c;__asm__ volatile("mrs %0,cntvct_el0":"=r"(c));return c;}
#define N 2000000
static uint32_t chain(uint32_t seed, uint32_t divisor){
  uint32_t x=seed;
  for(int i=0;i<N;i++){
    uint32_t q; __asm__ volatile("udiv %w0,%w1,%w2":"=r"(q):"r"(x),"r"(divisor));
    x = q + seed + 1;
  }
  return x;
}
int main(void){
  volatile uint32_t sink=0;
  uint32_t seeds[]={1,50,300,1000,3000,8000,50000,1000000,100000000u,4000000000u};
  printf("cntfrq=1.05GHz; N=%d serial udivs/class; ticks per udiv:\n",N);
  for(int s=0;s<10;s++){
    sink+=chain(seeds[s],3329);
    uint64_t best=~0ull;
    for(int rep=0;rep<5;rep++){
      uint64_t t0=cvt(); sink+=chain(seeds[s],3329); uint64_t t1=cvt();
      if(t1-t0<best) best=t1-t0;
    }
    printf("  dividend~%-11u  %.4f ticks/udiv\n",seeds[s],(double)best/N);
  }
  return sink==0xdeadbeefu?1:0;
}
