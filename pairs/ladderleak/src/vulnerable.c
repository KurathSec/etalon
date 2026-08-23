#include "scalarmul.h"
/* VULNERABLE ARM: ladder with a secret-dependent branch (LadderLeak, CCS 2020).
 *
 * Each ladder step branches on the current nonce bit, taking a different code
 * path (an extra dbl on the set-bit path). The sequence of taken branches, an
 * address-code / control-flow leak, depends on the secret nonce, which is what a
 * differential control-flow tool and a taint tool detect. A bit-length-dependent
 * cost is also present so the lattice recovery works. GROUND-TRUTH SITE. */
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  const EC_POINT *G = EC_GROUP_get0_generator(group);
  int bits = BN_num_bits(k);
  EC_POINT *R0 = EC_POINT_new(group), *R1 = EC_POINT_new(group);
  EC_POINT_set_to_infinity(group, R0); EC_POINT_copy(R1, G);
  for (int i = bits - 1; i >= 0; i--) {
    if (BN_is_bit_set(k, i)) {              /* SECRET-DEPENDENT branch: control flow leaks the bit */
      EC_POINT_add(group, R0, R0, R1, ctx);
      EC_POINT_dbl(group, R1, R1, ctx);
    } else {
      EC_POINT_dbl(group, R0, R0, ctx);
      EC_POINT_add(group, R1, R0, R1, ctx);
    }
  }
  EC_POINT_copy(R, R0);
  { EC_POINT *tmp = EC_POINT_new(group); EC_POINT_copy(tmp, G);
    for (int j = 0; j < 120 * bits; j++) EC_POINT_dbl(group, tmp, tmp, ctx);
    EC_POINT_free(tmp); }
  EC_POINT_free(R0); EC_POINT_free(R1);
  return 1;
}
