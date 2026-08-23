/* Acquisition harness for the reproduced Minerva pair.
 *
 * Signs N messages on secp256r1 with the arm's scalar multiplication, times each
 * signature with rdtsc, and writes the Minerva CSV the lattice attack consumes.
 * The private key appears only on the header line, as upstream's format requires,
 * and is used by the oracle solely to cross-check the verifier, never fed to the
 * recovery. The timings are real, from the arm under test, so this is a tier-A
 * acquisition rather than an imported observation set.
 */
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/obj_mac.h>
#include <openssl/rand.h>
#include <openssl/sha.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <x86intrin.h>
#include "scalarmul.h"

static void hex(const unsigned char *b, int n, char *out) {
  for (int i = 0; i < n; i++) sprintf(out + 2*i, "%02x", b[i]);
}

int main(int argc, char **argv) {
  if (argc != 3) { fprintf(stderr, "usage: %s <n> <out.csv>\n", argv[0]); return 2; }
  long N = strtol(argv[1], NULL, 10);
  FILE *f = fopen(argv[2], "w");
  if (!f) { perror("fopen"); return 2; }

  BN_CTX *ctx = BN_CTX_new();
  EC_GROUP *group = EC_GROUP_new_by_curve_name(NID_X9_62_prime256v1);
  const BIGNUM *order = EC_GROUP_get0_order(group);

  /* keypair */
  BIGNUM *d = BN_new(); BN_rand_range(d, order);
  EC_POINT *Q = EC_POINT_new(group);
  scalar_mul(group, Q, d, ctx);              /* Q = d*G, using this arm */

  /* header: pubkey (uncompressed 65 bytes), data (32 bytes), priv (32 bytes) */
  unsigned char pub[65]; size_t publen =
    EC_POINT_point2oct(group, Q, POINT_CONVERSION_UNCOMPRESSED, pub, 65, ctx);
  unsigned char data[32]; RAND_bytes(data, 32);
  unsigned char dbytes[32]; BN_bn2binpad(d, dbytes, 32);
  char hpub[131], hdata[65], hpriv[65];
  hex(pub, (int)publen, hpub); hex(data, 32, hdata); hex(dbytes, 32, hpriv);
  fprintf(f, "%s %s %s\n", hpub, hdata, hpriv);

  /* message hash h = SHA256(data), as an integer mod n */
  unsigned char md[32]; SHA256(data, 32, md);
  BIGNUM *h = BN_bin2bn(md, 32, NULL); BN_mod(h, h, order, ctx);

  BIGNUM *k = BN_new(), *r = BN_new(), *s = BN_new(),
         *kinv = BN_new(), *rd = BN_new(), *x = BN_new();
  EC_POINT *R = EC_POINT_new(group);

  /* warmup */
  for (int w = 0; w < 500; w++) { BN_rand_range(k, order); scalar_mul(group, R, k, ctx); }

  for (long i = 0; i < N; i++) {
    do { BN_rand_range(k, order); } while (BN_is_zero(k));
    unsigned int aux;
    unsigned long long t0 = __rdtscp(&aux);
    scalar_mul(group, R, k, ctx);            /* the timed, leaking operation */
    unsigned long long t1 = __rdtscp(&aux);

    EC_POINT_get_affine_coordinates(group, R, x, NULL, ctx);
    BN_mod(r, x, order, ctx);
    if (BN_is_zero(r)) { i--; continue; }
    BN_mod_inverse(kinv, k, order, ctx);
    BN_mod_mul(rd, r, d, order, ctx);
    BN_mod_add(s, h, rd, order, ctx);
    BN_mod_mul(s, s, kinv, order, ctx);      /* s = k^{-1}(h + r d) */
    if (BN_is_zero(s)) { i--; continue; }

    char hr[65], hs[65];
    BN_bn2binpad(r, (unsigned char*)md, 32); hex(md, 32, hr);
    BN_bn2binpad(s, (unsigned char*)md, 32); hex(md, 32, hs);
    fprintf(f, "%s,%s,%llu\n", hr, hs, t1 - t0);
  }
  fclose(f);
  fprintf(stderr, "harness: wrote %ld signatures to %s\n", N, argv[2]);
  return 0;
}
