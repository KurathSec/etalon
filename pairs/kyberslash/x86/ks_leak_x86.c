#include <stdio.h>
#include <stdint.h>
#include <x86intrin.h>
#define KYBER_Q 3329
/* The real KyberSlash coeff_to_bit, with the division FORCED to a hardware idiv via
   inline asm. Forcing is necessary on this host because its gcc 16.1.1 lowers the
   division to a reciprocal multiply even at -Os, unlike the pinned gcc-12.2.0 in the
   emission map, which emits the idiv; this file measures what the idiv-emitting build
   does, two-class fixed-vs-random, directly comparable to the Graviton end-to-end. */
static uint16_t coeff_to_bit(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+KYBER_Q/2), q;
  __asm__ volatile("movl %1,%%eax\n\t xorl %%edx,%%edx\n\t divl %2\n\t movl %%eax,%0"
                   :"=r"(q):"r"(d),"r"((uint32_t)KYBER_Q):"eax","edx","cc");
  return (uint16_t)(q & 1);
}
static inline uint64_t rd(void){ unsigned a; return __rdtscp(&a); }
#define M 4000000
static uint64_t batch(int hi){
  volatile uint16_t sink=0; uint32_t rng=hi?0xBu:0xAu;
  _mm_lfence(); uint64_t t0=rd();
  for(int i=0;i<M;i++){
    rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
    uint16_t c = hi ? (uint16_t)(1664+(rng%1665)) : (uint16_t)(rng%833);
    sink+=coeff_to_bit(c);
  }
  return rd()-t0;
}
int main(void){
  batch(0);batch(1);
  uint64_t lo=~0ull,hi=~0ull;
  for(int r=0;r<11;r++){uint64_t a=batch(0),b=batch(1); if(a<lo)lo=a; if(b<hi)hi=b;}
  double lp=(double)lo/M, hp=(double)hi/M;
  printf("RESULT e2e_low %.5f\n",lp);
  printf("RESULT e2e_high %.5f\n",hp);
  printf("RESULT e2e_delta %.5f\n",hp-lp);
  printf("RESULT e2e_pct %.4f\n",(hp-lp)/lp*100.0);
  return 0;
}
