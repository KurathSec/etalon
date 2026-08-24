/* CERTIFIED CONSTANT-TIME NEGATIVE.
 *
 * check_tag runs machine-checked constant-time Curve25519 field arithmetic
 * (Fiat-Crypto) over the secret and candidate: a field multiply and a
 * constant-time conditional select whose condition is a secret bit. The
 * operations are branchless and index no memory on the secret, so a correct
 * analyser reports no leak. A finding here is a genuine false positive.
 *
 * The two arms of this pair are identical; there is no leaking body to patch. */
#include "tag.h"
#include "fiat_25519.h"


static void pack(fiat_25519_loose_field_element e, const uint8_t *b) {
  /* Spread 16 secret bytes across five 51-bit limbs, kept small enough to be a
   * valid loose field element. Constant-time: no data-dependent control or index. */
  for (int i = 0; i < 5; i++) {
    uint64_t v = 0;
    for (int j = 0; j < 3; j++)
      v |= (uint64_t)b[(i * 3 + j) % TAG_LEN] << (8 * j);
    e[i] = v;   /* < 2^24, well within the loose bound */
  }
}

int check_tag(const uint8_t *secret, const uint8_t *candidate) {
  fiat_25519_loose_field_element a, c;
  fiat_25519_tight_field_element prod, sel;
  pack(a, secret);
  pack(c, candidate);
  fiat_25519_carry_mul(prod, a, c);
  /* constant-time conditional select on a secret-derived condition */
  fiat_25519_uint1 cond = (fiat_25519_uint1)(secret[0] & 1u);
  fiat_25519_selectznz(sel, cond, prod, prod);
  uint8_t out = 0;
  for (int i = 0; i < 5; i++) out ^= (uint8_t)sel[i];
  return (int)(out & 1u);
}
