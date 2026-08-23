#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include <string.h>
#include "reject.h"
int sample_pos(const uint8_t*,size_t,uint32_t*);
void prepare_inputs(dudect_config_t*c,uint8_t*in,uint8_t*cl){
  for(size_t i=0;i<c->number_measurements;i++){
    cl[i]=randombit(); uint8_t*b=in+(size_t)i*c->chunk_size;
    if(cl[i]==0){memset(b,0,KEY_LEN); b[0]=8;}     /* low threshold: many draws */
    else{memset(b,0,KEY_LEN); b[0]=200;}           /* high threshold: few draws */
  }
}
static uint32_t g_rng=0x777; uint8_t do_one_computation(uint8_t*d){ return (uint8_t)sample_pos(d,0,&g_rng);}
int main(void){ dudect_config_t cf={.chunk_size=KEY_LEN,.number_measurements=1e5};
  dudect_ctx_t c; dudect_init(&c,&cf); dudect_state_t s=DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  for(int i=0;i<40&&s==DUDECT_NO_LEAKAGE_EVIDENCE_YET;i++) s=dudect_main(&c);
  dudect_free(&c); printf("DUDECT_VERDICT %s\n", s==DUDECT_LEAKAGE_FOUND?"LEAK":"NO_LEAK_EVIDENCE"); return 0;}
