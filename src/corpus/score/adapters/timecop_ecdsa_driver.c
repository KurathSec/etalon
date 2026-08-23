/* TIMECOP driver for the leaking ECDSA scalar multiplication.
 *
 * Poison the nonce, run scalar_mul once. The vulnerable arm's loop bound
 * BN_num_bits(k) reads the poisoned nonce, so memcheck reports a branch on
 * uninitialised (secret) data. The patched arm's loop bound is constant.
 */
#include <valgrind/memcheck.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <openssl/rand.h>
#include <stdio.h>
#include "scalarmul.h"

int main(void) {
  BN_CTX *ctx = BN_CTX_new();
  EC_GROUP *group = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
  EC_POINT *R = EC_POINT_new(group);
  const BIGNUM *order = EC_GROUP_get0_order(group);
  unsigned char kb[32]; RAND_bytes(kb, 32);
  VALGRIND_MAKE_MEM_UNDEFINED(kb, 32);           /* the nonce is the secret */
  BIGNUM *k = BN_bin2bn(kb, 32, NULL);
  BN_mod(k, k, order, ctx);
  if (BN_is_zero(k)) BN_one(k);
  scalar_mul(group, R, k, ctx);
  printf("TIMECOP_DONE\n");
  return 0;
}
