/* Acquisition-side probe: is libgcrypt's scalar multiplication timeable, and does
 * the public API discriminate 1.8.4 from 1.8.5? Link it against each version's
 * static libgcrypt (see acquire.sh for flags) and run pinned to one core. It
 * times gcry_mpi_ec_mul over a short scalar (top bits zero) and a full one, both
 * allocated in secure memory and randomised in place exactly as libgcrypt's own
 * signing nonce is, and prints the minimum cycle count per class.
 *
 * The result recorded in record.json: BOTH versions show the short scalar
 * multiplied in roughly half the cycles of the full one, i.e. the public
 * primitive leaks the scalar bit-length and is unchanged across the patch. The
 * Minerva fix (1.8.5) is a bit-length clamp inside the internal signing path,
 * which the public gcry_mpi_ec_mul does not reach, so this probe cannot separate
 * the builds and the pair is scored by end-to-end recovery instead. This is a
 * measurement, not a per-arm analyser verdict.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <gcrypt.h>
#include <x86intrin.h>

static uint64_t rd(void) { unsigned a; return __rdtscp(&a); }

int main(void) {
  gcry_check_version(NULL);
  gcry_control(GCRYCTL_INIT_SECMEM, 65536, 0);
  gcry_control(GCRYCTL_INITIALIZATION_FINISHED, 0);
  gcry_ctx_t ec;
  gcry_mpi_ec_new(&ec, NULL, "NIST P-256");
  gcry_mpi_point_t G = gcry_mpi_ec_get_point("g", ec, 1);
  gcry_mpi_point_t W = gcry_mpi_point_new(0);
  printf("libgcrypt %s\n", gcry_check_version(NULL));
  for (int cls = 0; cls < 2; cls++) {
    unsigned nb = cls ? 256 : 128;            /* full vs short (top 128 bits zero) */
    gcry_mpi_t k = gcry_mpi_snew(256);        /* secure memory, as the nonce is */
    uint64_t best = ~0ull;
    for (int r = 0; r < 3000; r++) {
      gcry_mpi_randomize(k, nb, GCRY_WEAK_RANDOM);   /* in place: stays secure */
      uint64_t t0 = rd();
      gcry_mpi_ec_mul(W, k, G, ec);
      uint64_t d = rd() - t0;
      if (d < best) best = d;
    }
    printf("class=%d nbits=%u min_cycles=%llu\n", cls, nb, (unsigned long long)best);
    gcry_mpi_release(k);
  }
  return 0;
}
