/* Settle the containment question by timing both regions in ONE process.
 *
 * The paper reports three figures for this case and says they are mutually
 * impossible: an isolated scalar-multiplication call, a whole signature that must
 * contain one, and a retired-instruction count for the call. The signature came out
 * CHEAPER than the call it contains, which cannot be true of the same quantity, so
 * at least one figure is not what its name says. Which one was undetermined, because
 * the three came from three different harnesses on three different runs.
 *
 * This measures them together: same process, same clock, same build, interleaved so
 * neither gets a warmed cache the other lacks. Whatever the answer is, it is now a
 * comparison between two numbers rather than between two runs.
 *
 * Regions timed:
 *   sign      psEccDsaSign end to end, which is what sign_mx.c times
 *   mulmod    eccMulmod with the per-call pstm_init_size/pstm_clear of the dudect
 *             harness's do_one_computation, which is what the harness times
 *   mulbare   eccMulmod with the scratch allocated once outside the timed region,
 *             which isolates what that per-call allocation costs
 *   genkey    psEccGenKey, which is where the SIGNING path gets its scalar
 *             multiplication: psEccDsaSignCommon generates an ephemeral key and
 *             ecc_keygen.c calls eccMulmod on it, so this is the deployed call
 *             rather than a reconstruction of one
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <x86intrin.h>
#include "coreApi.h"
#include "cryptoApi.h"

#ifndef NREP
#define NREP 2000
#endif

extern psEccPoint_t *eccNewPoint(psPool_t *pool, short size);
extern int32_t eccMulmod(psPool_t *pool, const pstm_int *k, const psEccPoint_t *G,
                         psEccPoint_t *R, pstm_int *modulus, uint8_t map,
                         pstm_int *tmp_int);

static uint64_t rd(void) { unsigned a; return __rdtscp(&a); }

static int cmp64(const void *a, const void *b) {
  uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
  return x < y ? -1 : x > y;
}
static void report(const char *name, uint64_t *v, int n) {
  qsort(v, n, sizeof *v, cmp64);
  double mean = 0; for (int i = 0; i < n; i++) mean += (double)v[i];
  /* The median and the 10th percentile are reported beside the mean because a
   * shared host's mean carries every interruption the run happened to catch. */
  printf("%-8s n=%d  min=%llu  p10=%llu  median=%llu  mean=%.0f  max=%llu\n",
         name, n, (unsigned long long)v[0], (unsigned long long)v[n / 10],
         (unsigned long long)v[n / 2], mean / n, (unsigned long long)v[n - 1]);
}

int main(void) {
  const psEccCurve_t *curve; psEccKey_t *key;
  if (psCryptoOpen(PSCRYPTO_CONFIG) < 0) return 2;
  if (getEccParamById(IANA_SECP256R1, &curve) < 0) return 2;
  if (psEccNewKey(NULL, &key, curve) < 0) return 2;
  if (psEccGenKey(NULL, key, curve, NULL) < 0) return 2;

  psEccPoint_t *G = eccNewPoint(NULL, key->pubkey.x.used + 1);
  psEccPoint_t *R = eccNewPoint(NULL, (key->pubkey.x.used * 2) + 1);
  pstm_int prime;
  pstm_init_for_read_unsigned_bin(NULL, &prime, curve->size);
  pstm_read_radix(NULL, &prime, curve->prime, (int32)strlen(curve->prime), 16);
  pstm_read_radix(NULL, &G->x, curve->Gx, (int32)strlen(curve->Gx), 16);
  pstm_read_radix(NULL, &G->y, curve->Gy, (int32)strlen(curve->Gy), 16);
  pstm_set(&G->z, 1);

  /* One full-length nonce, converted once, exactly as the harness does. */
  pstm_int k;
  unsigned char b[32];
  for (int i = 0; i < 32; i++) b[i] = (unsigned char)(i * 7 + 1);
  b[0] |= 0x80;
  pstm_init_for_read_unsigned_bin(NULL, &k, 32);
  pstm_read_unsigned_bin(&k, b, 32);

  unsigned char msg[32]; memset(msg, 0x5a, 32);
  unsigned char h[32];
  psSha256_t sha; psSha256Init(&sha); psSha256Update(&sha, msg, 32); psSha256Final(&sha, h);

  pstm_int scratch;
  pstm_init_size(NULL, &scratch, prime.alloc);

  uint64_t *ts = malloc(NREP * sizeof *ts);
  uint64_t *tm = malloc(NREP * sizeof *tm);
  uint64_t *tb = malloc(NREP * sizeof *tb);
  uint64_t *tg = malloc(NREP * sizeof *tg);
  uint64_t *tn = malloc(NREP * sizeof *tn);

  /* Warm: first calls pay page faults and cold caches that belong to neither region. */
  for (int i = 0; i < 50; i++) {
    unsigned char sig[160]; psSize_t sl = sizeof sig;
    psEccDsaSign(NULL, key, h, 32, sig, &sl, 0, NULL);
    eccMulmod(NULL, &k, G, R, &prime, 1, &scratch);
  }

  /* Interleaved, so a drift in machine state hits all three regions alike. */
  for (int i = 0; i < NREP; i++) {
    unsigned char sig[160]; psSize_t sl = sizeof sig;
    uint64_t a = rd();
    psEccDsaSign(NULL, key, h, 32, sig, &sl, 0, NULL);
    uint64_t c = rd();
    ts[i] = c - a;

    a = rd();
    { pstm_int tmp; pstm_init_size(NULL, &tmp, prime.alloc);
      eccMulmod(NULL, &k, G, R, &prime, 1, &tmp);
      pstm_clear(&tmp); }
    c = rd();
    tm[i] = c - a;

    a = rd();
    eccMulmod(NULL, &k, G, R, &prime, 1, &scratch);
    c = rd();
    tb[i] = c - a;

    /* The same call with the curve-parameter argument the LIBRARY passes. That
     * argument is not scratch: it is the curve's a coefficient, and secp256r1 is
     * flagged isOptimized (a = -3), so ecc_keygen.c never allocates it and passes
     * NULL, which selects the fast doubling. A non-NULL zero selects the generic
     * path for a = 0, which is a different curve and a different cost. */
    a = rd();
    eccMulmod(NULL, &k, G, R, &prime, 1, NULL);
    c = rd();
    tn[i] = c - a;

    /* The signing path's own scalar multiplication, called the way the library
     * calls it rather than the way a harness reconstructs it. */
    { psEccKey_t *ek;
      a = rd();
      psEccNewKey(NULL, &ek, curve);
      psEccGenKey(NULL, ek, curve, NULL);
      c = rd();
      tg[i] = c - a;
      psEccDeleteKey(&ek); }
  }

  report("sign", ts, NREP);
  report("mulmod", tm, NREP);
  report("mulbare", tb, NREP);
  report("mulnull", tn, NREP);
  report("genkey", tg, NREP);
  return 0;
}
