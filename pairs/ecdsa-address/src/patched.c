#include "scalarmul.h"
/* PATCHED ARM: OpenSSL's constant-time scalar multiplication. No secret-indexed
 * memory access and no bit-length-dependent iteration. Faithful to the real
 * fix (switch to a constant-time routine). */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  return EC_POINT_mul(group, R, k, NULL, NULL, ctx);
}
