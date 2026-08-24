/* CERTIFIED CONSTANT-TIME NEGATIVE (field add/sub/carry).
 *
 * check_tag runs machine-checked constant-time Curve25519 field addition,
 * subtraction and carry (Fiat-Crypto) over the secret and candidate. A distinct
 * certified-CT operation from certified-fiat's multiply-and-select. The operations
 * are branchless and index no memory on the secret, so a correct analyser reports
 * no leak; a finding here is a genuine false positive. Both arms are identical. */
#include "tag.h"
#include "fiat_25519.h"

static void packt(fiat_25519_tight_field_element e, const uint8_t *b) {
  /* 16 secret bytes spread across five limbs, kept small (a valid tight element).
     Constant-time: no data-dependent control or index. */
  for (int i = 0; i < 5; i++) {
    uint64_t v = 0;
    for (int j = 0; j < 3; j++)
      v |= (uint64_t)b[(i * 3 + j) % TAG_LEN] << (8 * j);
    e[i] = v;   /* < 2^24, within the tight bound */
  }
}

int check_tag(const uint8_t *secret, const uint8_t *candidate) {
  fiat_25519_tight_field_element a, c, out;
  fiat_25519_loose_field_element sum, diff;
  packt(a, secret);
  packt(c, candidate);
  fiat_25519_add(sum, a, c);
  fiat_25519_carry(out, sum);
  fiat_25519_sub(diff, out, a);
  fiat_25519_carry(out, diff);
  uint8_t r = 0;
  for (int i = 0; i < 5; i++) r ^= (uint8_t)out[i];
  return (int)(r & 1u);
}
