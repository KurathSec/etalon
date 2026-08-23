#include "scalarmul.h"
/* PATCHED ARM.
 *
 * Uses OpenSSL's constant-time scalar multiplication. This is faithful to the
 * real Minerva fix, which replaced the leaking scalar multiplication with a
 * constant-time one: neither the running time nor the operation sequence depends
 * on the nonce. An earlier version of this arm only made the loop COUNT
 * constant, which left the conditional point-addition branching on the nonce
 * bits; the analysers correctly flagged that residual leak, which is why this
 * arm now delegates to the library's constant-time routine rather than rolling
 * a partial fix. */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  return EC_POINT_mul(group, R, k, NULL, NULL, ctx);
}
