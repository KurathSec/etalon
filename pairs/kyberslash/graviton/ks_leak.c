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
/* Two classes: A = low coeffs [0,832], B = high coeffs [1664,3328].
   Operands are generated OUTSIDE the timed region, from the SAME seed, and both
   classes are timed by the same loop over a precomputed array. An earlier revision
   generated each class inside the timed loop with a different expression, `rng%833`
   against `1664+(rng%1665)`, and seeded the two classes differently. Those are two
   different constant-modulus reductions, each lowered to its own multiply-shift
   sequence, so the measured delta conflated the divider's operand dependence with the
   cost of generating the operands. Re-measuring the x86 twin after this correction
   took its delta from 1.65% to about zero, so any number this program produced before
   the correction is not an operand-magnitude measurement. */
#define M 4000000
static uint16_t *make_class(int hi, uint32_t seed){
  uint16_t *v = malloc((size_t)M * sizeof *v);
  uint32_t rng = seed;
  for (int i = 0; i < M; i++){
    rng ^= rng<<13; rng ^= rng>>17; rng ^= rng<<5;
    v[i] = hi ? (uint16_t)(1664 + (rng % 1665)) : (uint16_t)(rng % 833);
  }
  return v;
}
static uint64_t batch(const uint16_t *v){
  volatile uint16_t sink=0;
  uint64_t t0=cvt();
  for(int i=0;i<M;i++) sink += coeff_to_bit(v[i]);
  return cvt()-t0;
}
int main(void){
  uint16_t *lov = make_class(0, 0xA), *hiv = make_class(1, 0xA);
  batch(lov); batch(hiv);       /* warm */
  uint64_t lo=~0ull,hi=~0ull;
  for(int r=0;r<9;r++){uint64_t a=batch(lov),b=batch(hiv); if(a<lo)lo=a; if(b<hi)hi=b;}
  double lp=(double)lo/M, hp=(double)hi/M;
  printf("coeff_to_bit, real KyberSlash site, %d calls/class:\n",M);
  printf("  low  coeffs [0,832]     %.4f ticks/call\n",lp);
  printf("  high coeffs [1664,3328] %.4f ticks/call\n",hp);
  printf("  SECRET-DEPENDENT DELTA  %.4f ticks/call  (%.1f%% of call)\n",hp-lp,(hp-lp)/lp*100);
  printf("  verdict: %s\n", (hp-lp)>0.05? "LEAK MEASURABLE on Graviton3" : "below timer resolution");
  free(lov); free(hiv);
  return 0;
}
