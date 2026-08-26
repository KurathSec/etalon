/* Retired-instruction count per nonce class, under Callgrind.
 *
 * A timing difference alone cannot say whether two classes run different WORK or the
 * same work with different memory behaviour. Counting retired instructions settles it:
 * equal counts with a timing gap would point at the microarchitecture, unequal counts
 * point at the algorithm.
 *
 * This is the corrected driver. The earlier one passed a freshly allocated zero as
 * eccMulmod's last argument, which is not scratch but the curve's `a` coefficient, so
 * it counted instructions for scalar multiplication on a different curve. Its per-call
 * figure could not fit inside the measured call at any credible retire rate, and the
 * paper reported that as an unresolved contradiction. The deployed call passes NULL,
 * which selects the optimised a = -3 doubling.
 *
 * One nonce class per run, scalar fixed within the run, so the count is deterministic
 * and the classes are compared across runs rather than interleaved.
 *
 * Usage: icount <bits> <calls>
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "coreApi.h"
#include "cryptoApi.h"

extern psEccPoint_t *eccNewPoint(psPool_t *pool, short size);
extern int32_t eccMulmod(psPool_t *pool, const pstm_int *k, const psEccPoint_t *G,
                         psEccPoint_t *R, pstm_int *modulus, uint8_t map,
                         pstm_int *tmp_int);

static void set_bitlength(uint8_t *b, int nbits) {
  int top = nbits - 1;
  int byte = (255 - top) / 8, bit = 7 - ((255 - top) % 8);
  for (int i = 0; i < byte; i++) b[i] = 0;
  b[byte] &= (uint8_t)((1u << bit) - 1u);
  b[byte] |= (uint8_t)(1u << bit);
}

int main(int argc, char **argv) {
  int bits = argc > 1 ? atoi(argv[1]) : 256;
  int calls = argc > 2 ? atoi(argv[2]) : 200;
  const psEccCurve_t *curve; psEccKey_t *key;
  if (psCryptoOpen(PSCRYPTO_CONFIG) < 0) return 2;
  if (getEccParamById(IANA_SECP256R1, &curve) < 0) return 2;
  if (psEccNewKey(NULL, &key, curve) < 0) return 2;
  if (psEccGenKey(NULL, key, curve, NULL) < 0) return 2;

  psEccPoint_t *G = eccNewPoint(NULL, key->pubkey.x.used + 1);
  psEccPoint_t *R = eccNewPoint(NULL, (key->pubkey.x.used * 2) + 1);
  pstm_int prime;
  pstm_init_for_read_unsigned_bin(NULL, &prime, curve->size);
  pstm_read_radix(NULL, &prime, curve->prime, (int32) strlen(curve->prime), 16);
  pstm_read_radix(NULL, &G->x, curve->Gx, (int32) strlen(curve->Gx), 16);
  pstm_read_radix(NULL, &G->y, curve->Gy, (int32) strlen(curve->Gy), 16);
  pstm_set(&G->z, 1);

  uint8_t b[32];
  for (int i = 0; i < 32; i++) b[i] = (uint8_t)(i * 11 + 3);
  set_bitlength(b, bits);
  pstm_int k;
  pstm_init_for_read_unsigned_bin(NULL, &k, 32);
  pstm_read_unsigned_bin(&k, b, 32);
  fprintf(stderr, "bits=%d pstm_bits=%d used=%d calls=%d\n",
          bits, (int) pstm_count_bits(&k), (int) k.used, calls);

  for (int i = 0; i < calls; i++) {
    eccMulmod(NULL, &k, G, R, &prime, 1, NULL);   /* NULL: the deployed argument */
  }
  return 0;
}
