#include <stdio.h>
#include <stdint.h>
/* Latency across the ACTUAL KyberSlash operand range [0,8320], plus a CPU-freq
   calibration (busy-loop cntvct vs a known cycle count). */
static inline uint64_t cvt(void){uint64_t c;__asm__ volatile("mrs %0,cntvct_el0":"=r"(c));return c;}
#define N 4000000
static uint32_t chain(uint32_t seed,uint32_t d){uint32_t x=seed|1;
  for(int i=0;i<N;i++){uint32_t q;__asm__ volatile("udiv %w0,%w1,%w2":"=r"(q):"r"(x),"r"(d));x=q+seed+1;}
  return x;}
int main(void){
  volatile uint32_t sink=0;
  /* KyberSlash dividend = (coeff<<1)+1664, coeff in [0,3328] -> dividend in [1664,8320] */
  uint32_t divs[]={0,832,1664,3328,4992,6656,8320};  /* representing coeff 0..3328 */
  printf("KyberSlash operand range, divisor=3329, N=%d serial udivs:\n",N);
  double base=0;
  for(int s=0;s<7;s++){
    uint32_t dv=divs[s]+1;
    sink+=chain(dv,3329);
    uint64_t best=~0ull;
    for(int r=0;r<7;r++){uint64_t a=cvt();sink+=chain(dv,3329);uint64_t b=cvt();if(b-a<best)best=b-a;}
    double tpu=(double)best/N;
    if(s==0)base=tpu;
    printf("  dividend %-5u (coeff~%-4u)  %.4f ticks/udiv   +%.4f vs smallest\n",
           dv,divs[s]/2,tpu,tpu-base);
  }
  return sink==7u?1:0;
}
