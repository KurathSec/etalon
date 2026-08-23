#ifndef SCALARMUL_H
#define SCALARMUL_H
#include <openssl/ec.h>
#include <openssl/bn.h>
/* Compute R = k*G on the given group. The two arms differ only in this function.
 * Returns 1 on success. */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx);
#endif
