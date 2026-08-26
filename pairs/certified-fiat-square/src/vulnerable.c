/* CERTIFIED CONSTANT-TIME NEGATIVE (field squaring and scalar multiply).
 *
 * check_tag runs machine-checked constant-time Curve25519 field squaring and
 * small-scalar multiplication (Fiat-Crypto) over the secret and candidate. A third
 * distinct certified-CT operation shape: certified-fiat exercises the general
 * multiply and a conditional select, certified-fiat-add the add/sub/carry chain,
 * and this one the squaring path, which a compiler lowers differently from a
 * general multiply because both operands are the same value. The operations are
 * branchless and index no memory on the secret, so a correct analyser reports no
 * leak; a finding here is a genuine false positive. Both arms are identical. */
#include "tag.h"
#include "fiat_25519.h"

static void packt(fiat_25519_tight_field_element e, const uint8_t *b) {
  /* 16 secret bytes across five limbs, kept small enough to be a valid tight
     element. Constant-time: no data-dependent control flow and no secret index. */
  for (int i = 0; i < 5; i++) {
    uint64_t v = 0;
    for (int j = 0; j < 3; j++)
      v |= (uint64_t)b[(i * 3 + j) % TAG_LEN] << (8 * j);
    e[i] = v;   /* < 2^24, within the tight bound */
  }
}

int check_tag(const uint8_t *secret, const uint8_t *candidate) {
  fiat_25519_tight_field_element a, c, sq, sc;
  fiat_25519_loose_field_element la, lc;
  packt(a, secret);
  packt(c, candidate);
  fiat_25519_relax(la, a);
  fiat_25519_relax(lc, c);
  fiat_25519_carry_square(sq, la);          /* squaring, not a general multiply */
  fiat_25519_carry_scmul_121666(sc, lc);    /* multiply by a fixed small scalar */
  uint8_t r = 0;
  for (int i = 0; i < 5; i++) r ^= (uint8_t)(sq[i] ^ sc[i]);
  return (int)(r & 1u);
}
