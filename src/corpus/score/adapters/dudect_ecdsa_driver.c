/* dudect driver for the leaking ECDSA scalar multiplication.
 *
 * Two-class test on the nonce: class 0 uses a fixed short nonce, class 1 a
 * random full-length nonce. If scalar_mul's time depends on the nonce
 * bit-length, the two classes have different timing distributions and dudect
 * reports leakage. The chunk is 32 bytes, one scalar.
 */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <string.h>
#include "scalarmul.h"

static EC_GROUP *group; static BN_CTX *ctx; static EC_POINT *R;

void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes) {
  for (size_t i = 0; i < c->number_measurements; i++) {
    classes[i] = randombit();
    uint8_t *b = input_data + (size_t)i * c->chunk_size;
    if (classes[i] == 0) { memset(b, 0, 32); b[31] = 0x01; b[30] = 0x02; }  /* short */
    else randombytes(b, 32);                                                 /* full */
  }
}

uint8_t do_one_computation(uint8_t *data) {
  BIGNUM *k = BN_bin2bn(data, 32, NULL);
  const BIGNUM *order = EC_GROUP_get0_order(group);
  BN_mod(k, k, order, ctx);
  if (BN_is_zero(k)) BN_one(k);
  scalar_mul(group, R, k, ctx);
  uint8_t r = (uint8_t)BN_is_bit_set(k, 0);
  BN_free(k);
  return r;
}

int main(void) {
  ctx = BN_CTX_new();
  group = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
  R = EC_POINT_new(group);
  dudect_config_t config = { .chunk_size = 32, .number_measurements = 2e4 };
  dudect_ctx_t c; dudect_init(&c, &config);
  dudect_state_t s = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  for (int i = 0; i < 40 && s == DUDECT_NO_LEAKAGE_EVIDENCE_YET; i++) s = dudect_main(&c);
  dudect_free(&c);
  printf("DUDECT_VERDICT %s\n", s == DUDECT_LEAKAGE_FOUND ? "LEAK" : "NO_LEAK_EVIDENCE");
  return 0;
}
