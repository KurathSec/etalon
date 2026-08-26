/* dudect driver for MatrixSSL's ECC scalar multiplication (Minerva, CVE-2019-13629).
 * Classes differ by one bit of nonce length (255 vs 256). All bignum conversion is
 * done in prepare_inputs, outside the timed region; the chunk carries an index. */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include "dudect_run.h"
#include "coreApi.h"
#include "cryptoApi.h"
#include <stdlib.h>
#include <string.h>

#define CHUNK 32
static psEccKey_t *key;
static psEccPoint_t *G, *R;
static pstm_int prime, A;
static pstm_int *pre = NULL; static size_t npre = 0;
static int same_len = 0;

extern psEccPoint_t *eccNewPoint(psPool_t *pool, short size);
extern int32_t eccMulmod(psPool_t *pool, const pstm_int *k, const psEccPoint_t *G,
                         psEccPoint_t *R, pstm_int *modulus, uint8_t map,
                         pstm_int *tmp_int);

void prepare_inputs(dudect_config_t *c, uint8_t *in, uint8_t *cl) {
  if (pre) { for (size_t i=0;i<npre;i++) pstm_clear(&pre[i]); free(pre); }
  npre = c->number_measurements; pre = calloc(npre, sizeof *pre);
  uint8_t b[32];
  for (size_t i = 0; i < npre; i++) {
    cl[i] = randombit();
    randombytes(b, 32);
    /* CONTROL=same makes both classes 256-bit, differing only in value: if the
       residual is bit-length dependence it must vanish here, and if it does not
       the signal is in the harness rather than in the library. */
    b[0] = same_len ? 0x80 : (cl[i] ? 0x80 : 0x40);
    pstm_init_for_read_unsigned_bin(NULL, &pre[i], 32);
    pstm_read_unsigned_bin(&pre[i], b, 32);
    memcpy(in + (size_t)i * c->chunk_size, &i, sizeof i);
  }
}
uint8_t do_one_computation(uint8_t *data) {
  size_t idx; memcpy(&idx, data, sizeof idx);
  pstm_int tmp;
  pstm_init_size(NULL, &tmp, prime.alloc);
  eccMulmod(NULL, &pre[idx], G, R, &prime, 1, &tmp);
  pstm_clear(&tmp);
  return 0;
}
int main(void) {
  const psEccCurve_t *curve;
  { const char *e = getenv("CONTROL"); same_len = e && !strcmp(e, "same"); }
  if (psCryptoOpen(PSCRYPTO_CONFIG) < 0) return 2;
  if (getEccParamById(IANA_SECP256R1, &curve) < 0) return 2;
  if (psEccNewKey(NULL, &key, curve) < 0) return 2;
  if (psEccGenKey(NULL, key, curve, NULL) < 0) return 2;
  G = eccNewPoint(NULL, key->pubkey.x.used + 1);
  R = eccNewPoint(NULL, (key->pubkey.x.used * 2) + 1);
  pstm_init_for_read_unsigned_bin(NULL, &prime, curve->size);
  pstm_read_radix(NULL, &prime, curve->prime, (int32)strlen(curve->prime), 16);
  pstm_init_for_read_unsigned_bin(NULL, &A, curve->size);
  pstm_read_radix(NULL, &G->x, curve->Gx, (int32)strlen(curve->Gx), 16);
  pstm_read_radix(NULL, &G->y, curve->Gy, (int32)strlen(curve->Gy), 16);
  pstm_set(&G->z, 1);
  dudect_config_t config = { .chunk_size = CHUNK, .number_measurements = 20000 };
  return dudect_run_and_dump(&config);
}
