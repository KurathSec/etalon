#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#define KYBER_Q 3329
static inline uint64_t cvt(void){uint64_t c;__asm__ volatile("mrs %0,cntvct_el0":"=r"(c));return c;}
/* the real KyberSlash coeff_to_bit, forced to -Os codegen via the udiv */
static uint16_t coeff_to_bit(uint16_t t){
  t += ((int16_t)t >> 15) & KYBER_Q;
  uint32_t d=(uint32_t)((t<<1)+KYBER_Q/2), q;
  __asm__ volatile("udiv %w0,%w1,%w2":"=r"(q):"r"(d),"r"((uint32_t)KYBER_Q));
  return (uint16_t)(q & 1);
}
/* dudect-style: class A = low coeffs [0,832], class B = high coeffs [1664,3328] */
#define M 4000000
static uint64_t batch(int hi){
  volatile uint16_t sink=0; uint32_t rng=hi?0xB:0xA;
  uint64_t t0=cvt();
  for(int i=0;i<M;i++){
    rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
    uint16_t c = hi ? (1664+(rng%1665)) : (rng%833);
    sink+=coeff_to_bit(c);
  }
  return cvt()-t0;
}
int main(void){
  batch(0);batch(1);            /* warm */
  uint64_t lo=~0ull,hi=~0ull;
  for(int r=0;r<9;r++){uint64_t a=batch(0),b=batch(1); if(a<lo)lo=a; if(b<hi)hi=b;}
  double lp=(double)lo/M, hp=(double)hi/M;
  printf("coeff_to_bit, real KyberSlash site, %d calls/class:\n",M);
  printf("  low  coeffs [0,832]     %.4f ticks/call\n",lp);
  printf("  high coeffs [1664,3328] %.4f ticks/call\n",hp);
  printf("  SECRET-DEPENDENT DELTA  %.4f ticks/call  (%.1f%% of call)\n",hp-lp,(hp-lp)/lp*100);
  printf("  verdict: %s\n", (hp-lp)>0.05? "LEAK MEASURABLE on Graviton3" : "below timer resolution");
  return 0;
}
