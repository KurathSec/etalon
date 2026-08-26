/* Amplification, overridable at build time with -DAMP=n so the registered
 * detection curve can sweep it. The default is the committed value: an
 * unparameterised build of this file is byte-for-byte what it was. */
#ifndef AMP
#define AMP 40
#endif
#include "scalarmul.h"
/* VULNERABLE ARM. Reproduces the Minerva mechanism (CVE-2019-13627).
 *
 * Double-and-add over exactly BN_num_bits(k) bits. The loop count is the
 * nonce's bit-length, so both the running time and the number of point
 * operations leak it. This is the leak Minerva exploited in libgcrypt: a
 * scalar multiplication whose work is proportional to the bit-length of a
 * secret nonce. GROUND-TRUTH SITE. */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  int bits = BN_num_bits(k);                 /* SECRET-DEPENDENT loop bound */
  const EC_POINT *G = EC_GROUP_get0_generator(group);
  if (!EC_POINT_set_to_infinity(group, R)) return 0;
  EC_POINT *tmp = EC_POINT_new(group);
  if (!tmp || !EC_POINT_copy(tmp, G)) { EC_POINT_free(tmp); return 0; }
  for (int i = 0; i < bits; i++) {            /* runs bitlen(k) times: the leak */
    if (BN_is_bit_set(k, i)) {
      if (!EC_POINT_add(group, R, R, tmp, ctx)) { EC_POINT_free(tmp); return 0; }
    }
    if (!EC_POINT_dbl(group, tmp, tmp, ctx)) { EC_POINT_free(tmp); return 0; }
  }
  /* Amplify the per-scalar-mul cost so the bit-length signal dominates rdtsc
   * noise on a fast x86 core. This widens the leak; it does not create it. The
   * work is still proportional to the loop bound, which is the point. */
  for (int j = 0; j < AMP * bits; j++) { EC_POINT_dbl(group, tmp, tmp, ctx); }
  EC_POINT_free(tmp);
  return 1;
}
