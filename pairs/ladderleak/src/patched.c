#include "scalarmul.h"
/* PATCHED ARM: OpenSSL constant-time mul, no secret-dependent branch. */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  return EC_POINT_mul(group, R, k, NULL, NULL, ctx);
}
