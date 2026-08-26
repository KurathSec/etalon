/* CERTIFIED CONSTANT-TIME NEGATIVE (field serialisation).
 *
 * check_tag runs machine-checked constant-time Curve25519 serialisation
 * (Fiat-Crypto from_bytes and to_bytes) over the secret and candidate. This is the
 * operation shape most likely to draw a false positive from an address-sensitive
 * analyser, because serialisation writes a byte array in a loop and a checker that
 * reasons coarsely about memory can mistake a fixed-stride write for a
 * secret-dependent one. It is not: the stride and the trip count are constants and
 * only the VALUES written depend on the secret, which is what a correct
 * constant-time policy permits. A finding here is a genuine false positive, and it
 * is the case worth having in the denominator. Both arms are identical. */
#include "tag.h"
#include "fiat_25519.h"

int check_tag(const uint8_t *secret, const uint8_t *candidate) {
  uint8_t sbuf[32], cbuf[32], out[32];
  fiat_25519_tight_field_element a, c;
  fiat_25519_loose_field_element sum;
  fiat_25519_tight_field_element red;

  /* Fixed-width copies: the loop bounds are constants, the indices are not secret. */
  for (int i = 0; i < 32; i++) {
    sbuf[i] = secret[i % TAG_LEN];
    cbuf[i] = candidate[i % TAG_LEN];
  }
  sbuf[31] &= 0x7f;   /* from_bytes expects the top bit clear */
  cbuf[31] &= 0x7f;

  fiat_25519_from_bytes(a, sbuf);
  fiat_25519_from_bytes(c, cbuf);
  fiat_25519_add(sum, a, c);
  fiat_25519_carry(red, sum);
  fiat_25519_to_bytes(out, red);

  uint8_t r = 0;
  for (int i = 0; i < 32; i++) r ^= out[i];
  return (int)(r & 1u);
}
