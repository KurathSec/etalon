#include "scalarmul.h"
/* VULNERABLE ARM: secret-indexed table access (address leak) plus a
 * bit-length-dependent window count (timing leak).
 *
 * A precomputed table of small multiples of G is indexed by successive secret
 * nonce digits, so the sequence of memory addresses accessed depends on the
 * secret (the address-trace leak a differential tool detects). The number of
 * windows processed is the nonce bit-length in windows, so time also leaks the
 * bit-length (the lattice recovery uses this). GROUND-TRUTH SITE. */
#define WBITS 4
#define TSIZE (1 << WBITS)
int scalar_mul(EC_GROUP *group, EC_POINT *R, const BIGNUM *k, BN_CTX *ctx) {
  const EC_POINT *G = EC_GROUP_get0_generator(group);
  EC_POINT *tab[TSIZE];
  for (int i = 0; i < TSIZE; i++) {
    tab[i] = EC_POINT_new(group);
    BIGNUM *m = BN_new(); BN_set_word(m, i);
    EC_POINT_mul(group, tab[i], NULL, G, m, ctx);   /* tab[i] = i*G */
    BN_free(m);
  }
  int bits = BN_num_bits(k);                        /* secret-dependent window count */
  int nwin = (bits + WBITS - 1) / WBITS;
  if (!EC_POINT_set_to_infinity(group, R)) goto done;
  for (int w = nwin - 1; w >= 0; w--) {
    for (int d = 0; d < WBITS; d++) EC_POINT_dbl(group, R, R, ctx);
    int digit = 0;                                  /* the secret window digit */
    for (int b = 0; b < WBITS; b++)
      if (BN_is_bit_set(k, w*WBITS + b)) digit |= (1 << b);
    EC_POINT_add(group, R, R, tab[digit], ctx);     /* SECRET-INDEXED table access */
  }
  /* Amplify a bit-length-proportional cost so the timing side channel cleanly
   * leaks BN_num_bits(k) for the lattice recovery, exactly as the ecdsa-nonce
   * pair does. This is the recovery channel; the secret-indexed table access
   * above is the address channel the differential tools detect. The pair thus
   * carries both an address leak (its declared mechanism) and a timing leak
   * (its recovery), which is faithful to windowed implementations that leak
   * both. */
  {
    EC_POINT *tmp = EC_POINT_new(group);
    EC_POINT_copy(tmp, G);
    for (int j = 0; j < 40 * bits; j++) EC_POINT_dbl(group, tmp, tmp, ctx);
    EC_POINT_free(tmp);
  }
done:
  for (int i = 0; i < TSIZE; i++) EC_POINT_free(tab[i]);
  return 1;
}
