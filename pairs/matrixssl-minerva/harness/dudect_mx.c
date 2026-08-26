/* dudect driver for MatrixSSL's ECC scalar multiplication (Minerva, CVE-2019-13629).
 * Classes differ in the nonce's BIT LENGTH, by an amount the CONTROL design fixes;
 * see the design table below. All bignum conversion is done in prepare_inputs,
 * outside the timed region, and the chunk carries an index rather than a value. */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include "dudect_run.h"
#include "coreApi.h"
#include "cryptoApi.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHUNK 32
static psEccKey_t *key;
static psEccPoint_t *G, *R;
static pstm_int prime;
static pstm_int *pre = NULL; static size_t npre = 0;

/* The four designs the paper reports, selected by CONTROL. Class 1 is always a
 * full-length 256-bit nonce; the mode fixes what class 0 is, and every design
 * holds everything else constant so the two classes differ in exactly one thing.
 *
 *   same       256 vs 256   the control. Both classes full length, differing only
 *                           in value. If the residual is bit-length dependence it
 *                           must vanish here; if it does not, the signal is in the
 *                           harness rather than in the library.
 *   bit255     255 vs 256   one leading zero. The default, and the headline.
 *   samedigit  193 vs 256   sixty-three leading zeros, but a pstm digit is 64 bits
 *                           on this build so BOTH occupy four digits and run the
 *                           identical loop bound. This is what separates the
 *                           leading-zero phase from the loop bound.
 *   diffdigit  192 vs 256   one bit shorter again, which drops class 0 to three
 *                           digits and DOES change the loop bound. The upper
 *                           bound on the mechanism, and 2^-64 likely in practice.
 *
 * An earlier revision of this harness carried only `same` and the default, so the
 * two designs that separate the phase from the bound could not be reproduced from
 * anything the repository held. They can now. */
enum { D_BIT255 = 0, D_SAME, D_SAMEDIGIT, D_DIFFDIGIT };
static int design = D_BIT255;

/* Set b to a big-endian 32-byte value whose highest set bit is bit (nbits-1),
 * leaving the bits below it as drawn. Bit 255 is the most significant bit of
 * b[0], so bit n lives in byte (255-n)/8 at position 7-((255-n)%8). */
static void set_bitlength(uint8_t *b, int nbits) {
  int top = nbits - 1;
  int byte = (255 - top) / 8, bit = 7 - ((255 - top) % 8);
  for (int i = 0; i < byte; i++) b[i] = 0;          /* everything above is zero */
  b[byte] &= (uint8_t)((1u << bit) - 1u);           /* clear above the top bit  */
  b[byte] |= (uint8_t)(1u << bit);                  /* and set the top bit      */
}

extern psEccPoint_t *eccNewPoint(psPool_t *pool, short size);
extern int32_t eccMulmod(psPool_t *pool, const pstm_int *k, const psEccPoint_t *G,
                         psEccPoint_t *R, pstm_int *modulus, uint8_t map,
                         pstm_int *tmp_int);

void prepare_inputs(dudect_config_t *c, uint8_t *in, uint8_t *cl) {
  if (pre) { for (size_t i=0;i<npre;i++) pstm_clear(&pre[i]); free(pre); }
  npre = c->number_measurements; pre = calloc(npre, sizeof *pre);
  uint8_t b[32];
  for (size_t i = 0; i < npre; i++) {
    cl[i] = randombit();
    randombytes(b, 32);
    /* Class 1 is full length in every design; class 0 is what the design varies. */
    if (cl[i]) {
      set_bitlength(b, 256);
    } else {
      switch (design) {
        case D_SAME:      set_bitlength(b, 256); break;
        case D_SAMEDIGIT: set_bitlength(b, 193); break;
        case D_DIFFDIGIT: set_bitlength(b, 192); break;
        default:          set_bitlength(b, 255); break;
      }
    }
    pstm_init_for_read_unsigned_bin(NULL, &pre[i], 32);
    pstm_read_unsigned_bin(&pre[i], b, 32);
    memcpy(in + (size_t)i * c->chunk_size, &i, sizeof i);
  }
}
uint8_t do_one_computation(uint8_t *data) {
  size_t idx; memcpy(&idx, data, sizeof idx);
  /* The last argument is NOT scratch. It is the curve's `a` coefficient, handed
   * through to eccProjectiveDblPoint, and secp256r1 is flagged isOptimized in
   * ecc_curve_data.c ("1 if optimized with field parameter A=-3"), so
   * ecc_keygen.c never allocates it and the deployed call passes NULL. NULL
   * selects the fast a = -3 doubling; a non-NULL zero selects the generic path
   * for a = 0, which is a different curve and 3.46x the cost of the deployed call
   * (3.42x the library's own key generation).
   *
   * An earlier revision of this harness passed a freshly allocated zero here and
   * so timed scalar multiplication on the wrong curve. That is what made the
   * isolated call cost more than a whole signature containing one, which the
   * paper reported as an unresolved contradiction between three figures.
   * Measured together in one process, eccMulmod with NULL and psEccGenKey agree
   * to within 1.03%. See pairs/matrixssl-minerva/acquire/containment.c. */
  eccMulmod(NULL, &pre[idx], G, R, &prime, 1, NULL);
  return 0;
}
int main(void) {
  const psEccCurve_t *curve;
  { const char *e = getenv("CONTROL");
    if (!e || !*e)                     design = D_BIT255;
    else if (!strcmp(e, "same"))       design = D_SAME;
    else if (!strcmp(e, "bit255"))     design = D_BIT255;
    else if (!strcmp(e, "samedigit"))  design = D_SAMEDIGIT;
    else if (!strcmp(e, "diffdigit"))  design = D_DIFFDIGIT;
    else { fprintf(stderr, "unknown CONTROL=%s\n", e); return 2; } }
  if (psCryptoOpen(PSCRYPTO_CONFIG) < 0) return 2;
  if (getEccParamById(IANA_SECP256R1, &curve) < 0) return 2;
  if (psEccNewKey(NULL, &key, curve) < 0) return 2;
  if (psEccGenKey(NULL, key, curve, NULL) < 0) return 2;
  G = eccNewPoint(NULL, key->pubkey.x.used + 1);
  R = eccNewPoint(NULL, (key->pubkey.x.used * 2) + 1);
  pstm_init_for_read_unsigned_bin(NULL, &prime, curve->size);
  pstm_read_radix(NULL, &prime, curve->prime, (int32)strlen(curve->prime), 16);
  pstm_read_radix(NULL, &G->x, curve->Gx, (int32)strlen(curve->Gx), 16);
  pstm_read_radix(NULL, &G->y, curve->Gy, (int32)strlen(curve->Gy), 16);
  pstm_set(&G->z, 1);
  dudect_config_t config = { .chunk_size = CHUNK, .number_measurements = 20000 };
  return dudect_run_and_dump(&config);
}
