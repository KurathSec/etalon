/* dudect driver for the leaking ECDSA scalar multiplication.
 *
 * Two-class test on the nonce's bit length, in the regime the Minerva attack
 * actually exploits: class 0 is a 255-bit nonce, class 1 a 256-bit one. Both are
 * uniformly random below the group order and both occupy the same number of
 * BIGNUM words, so the only difference between the classes is the position of the
 * leading bit. If the scalar multiplication's work is proportional to
 * BN_num_bits(k), the classes separate.
 *
 * Two things here are load-bearing, and both were wrong in an earlier revision:
 *
 *   * The BIGNUM conversion and reduction happen in prepare_inputs, OUTSIDE the
 *     timed region. BN_bin2bn and BN_mod are themselves variable-time in the
 *     magnitude of their input, and timing them alongside the site under test put
 *     a larger signal into the measurement than the site itself carried: measured
 *     on the patched arm, the conversion alone reached tau 1.78 while the whole
 *     arm read 0.379. do_one_computation now times the scalar multiplication and
 *     nothing else. The chunk carries an index into the pre-converted scalars.
 *
 *   * The classes differ by one bit, not by a whole word. An earlier revision used
 *     a ~10-bit scalar against a 256-bit one, which is not a nonce distribution any
 *     attacker sees: with a 10-bit scalar every operation touching it is cheaper,
 *     including the conversion and the BIGNUM's own footprint, so a constant-time
 *     implementation was reported as leaking. Under the one-bit design the patched
 *     arm reads clean (tau 0.0075, inside the calibrated null band) and the
 *     vulnerable arm leaks (tau 0.596), which is the discrimination the pair exists
 *     to measure.
 */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include "dudect_run.h"
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <stdlib.h>
#include <string.h>
#include "scalarmul.h"

static EC_GROUP *group; static BN_CTX *ctx; static EC_POINT *R;
static BIGNUM **pre = NULL; static size_t npre = 0;

void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes) {
  if (pre) { for (size_t i = 0; i < npre; i++) BN_free(pre[i]); free(pre); }
  npre = c->number_measurements;
  pre = calloc(npre, sizeof *pre);
  uint8_t b[32];
  for (size_t i = 0; i < npre; i++) {
    classes[i] = randombit();
    randombytes(b, 32);
    /* Top byte fixed so the value stays below the group order in both classes:
     * class 1 sets bit 255 (a 256-bit nonce), class 0 sets bit 254 (255-bit). */
    b[0] = classes[i] ? 0x80 : 0x40;
    pre[i] = BN_bin2bn(b, 32, NULL);
    /* The chunk carries only an index: no secret-dependent work in the timed path. */
    memcpy(input_data + (size_t)i * c->chunk_size, &i, sizeof i);
  }
}

uint8_t do_one_computation(uint8_t *data) {
  size_t idx;
  memcpy(&idx, data, sizeof idx);
  scalar_mul(group, R, pre[idx], ctx);
  return 0;
}

int main(void) {
  ctx = BN_CTX_new();
  group = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
  R = EC_POINT_new(group);
  dudect_config_t config = { .chunk_size = 32, .number_measurements = 2e4 };
  return dudect_run_and_dump(&config);
}
