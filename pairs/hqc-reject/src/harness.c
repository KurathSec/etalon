/* Acquisition harness. Byte-identical across arms. For each of many trials and
 * each key position, times sample_pos and emits the cycle count. The secret is
 * from /dev/urandom, printed once to a side file (hashed into the verifier,
 * then destroyed), never committed. Layout: [KEY_LEN][trials] u32, C order. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <x86intrin.h>
#include "reject.h"
int main(int argc,char**argv){
  if(argc!=4){fprintf(stderr,"usage: %s <trials> <out.bin> <secret.out>\n",argv[0]);return 2;}
  long trials=strtol(argv[1],NULL,10);
  if(trials<=0||trials>2000000){fprintf(stderr,"bad trials\n");return 2;}
  uint8_t secret[KEY_LEN];
  FILE*ur=fopen("/dev/urandom","rb"); if(!ur||fread(secret,1,KEY_LEN,ur)!=KEY_LEN){fprintf(stderr,"urandom\n");return 2;} fclose(ur);
  FILE*f=fopen(argv[2],"wb"); if(!f){perror("fopen");return 2;}
  uint32_t rng=0x1234567u;
  for(int w=0;w<2000;w++){sample_pos(secret,0,&rng);}    /* warmup */
  uint32_t*row=malloc((size_t)trials*sizeof(uint32_t));
  for(size_t pos=0;pos<KEY_LEN;pos++){
    for(long t=0;t<trials;t++){
      rng = (uint32_t)(t*2654435761u + 1);   /* per-trial reseed, matched in calibration */
      unsigned aux; uint64_t t0=__rdtscp(&aux);
      sample_pos(secret,pos,&rng);
      uint64_t t1=__rdtscp(&aux);
      uint64_t d=t1-t0; row[t]=(uint32_t)(d>0xffffffffu?0xffffffffu:d);
    }
    fwrite(row,sizeof(uint32_t),(size_t)trials,f);
  }
  free(row); fclose(f);
  FILE*sf=fopen(argv[3],"wb"); if(!sf){perror("secret");return 2;} fwrite(secret,1,KEY_LEN,sf); fclose(sf);

  /* Public calibration curve: mean cycles for KNOWN thresholds, written to a
   * companion .cal file. Uses no secret; a real attacker builds this on their
   * own copy of the implementation. Format: "thr mean\n" lines. */
  char calname[4096]; snprintf(calname,sizeof calname,"%s.cal",argv[2]);
  FILE*cf=fopen(calname,"w"); if(!cf){perror("cal");return 2;}
  for(int thr=2; thr<=254; thr+=2){
    uint8_t cs[KEY_LEN]; for(size_t j=0;j<KEY_LEN;j++) cs[j]=(uint8_t)thr;
    uint64_t sum=0; for(long tt=0;tt<trials;tt++){ rng=(uint32_t)(tt*2654435761u + 0 + 1); unsigned aux; uint64_t a=__rdtscp(&aux); sample_pos(cs,0,&rng); uint64_t b=__rdtscp(&aux); sum+=(b-a);}
    fprintf(cf,"%d %.2f\n",thr,(double)sum/(double)trials);
  }
  fclose(cf);
  fprintf(stderr,"harness: wrote %s (%d x %ld) + %s\n",argv[2],KEY_LEN,trials,calname);
  return 0;
}
