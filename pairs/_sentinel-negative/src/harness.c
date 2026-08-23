/* Acquisition harness. Byte-identical across both arms of the pair.
 *
 * Emits a cycle-count array and nothing else. In particular it never emits the
 * queries it made, and that is load-bearing rather than incidental: the probe
 * for position k uses the true prefix of the secret, so a transcript containing
 * the queries would contain the answer, and an offline "recovery" could read it
 * off instead of analysing anything. Storing only timings means the recorded
 * observations carry the secret exactly the way the side channel does, and a
 * recovery that ignores them cannot succeed.
 *
 * Layout, little-endian uint32, C order:
 *     [TAG_LEN][256][reps]
 * so element (k, g, r) is repetition r of a probe whose first k bytes are the
 * true prefix, whose byte k is the guess g, and whose remainder is zero.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <x86intrin.h>
#include "tag.h"

/* The secret is drawn from the operating system at acquisition time and is
 * never derivable from anything this repository commits.
 *
 * An earlier version of this file derived it from a seed constant in the
 * source. That looked reproducible and was in fact circular: the seed is
 * committed, so a "recovery" could compute the answer directly and never read a
 * single timing, and the oracle would still have said it verified. The trace is
 * supposed to be the only channel carrying the secret, and a committed seed is
 * a second one.
 *
 * So: acquisition generates the key, writes it out once for the caller to hash
 * into the published verifier, and the caller then destroys it. What is
 * committed afterwards is the timings and a digest, and neither yields the key
 * except through the side channel. */
static void derive_secret(uint8_t *out)
{
    FILE *ur = fopen("/dev/urandom", "rb");
    if (!ur || fread(out, 1, TAG_LEN, ur) != TAG_LEN) {
        fprintf(stderr, "harness: cannot read /dev/urandom\n");
        exit(2);
    }
    fclose(ur);
}

int main(int argc, char **argv)
{
    if (argc != 4) {
        fprintf(stderr, "usage: %s <reps> <out.bin> <secret.out>\n", argv[0]);
        return 2;
    }
    long reps = strtol(argv[1], NULL, 10);
    if (reps <= 0 || reps > 100000) { fprintf(stderr, "bad reps\n"); return 2; }

    uint8_t secret[TAG_LEN], cand[TAG_LEN];
    derive_secret(secret);

    FILE *f = fopen(argv[2], "wb");
    if (!f) { perror("fopen"); return 2; }

    /* Warm the caches and the branch predictor before anything is recorded.
     * Discarding nothing at all is how a first-measurement artefact becomes a
     * finding. */
    for (int w = 0; w < 2000; w++) {
        memset(cand, 0, TAG_LEN);
        check_tag(secret, cand);
    }

    uint32_t *row = malloc((size_t)reps * sizeof(uint32_t));
    if (!row) return 2;

    for (size_t k = 0; k < TAG_LEN; k++) {
        for (int g = 0; g < 256; g++) {
            memset(cand, 0, TAG_LEN);
            memcpy(cand, secret, k);          /* the true prefix */
            cand[k] = (uint8_t)g;             /* the guess under test */
            for (long r = 0; r < reps; r++) {
                unsigned int aux;
                uint64_t t0 = __rdtscp(&aux);
                check_tag(secret, cand);
                uint64_t t1 = __rdtscp(&aux);
                uint64_t d = t1 - t0;
                row[r] = (uint32_t)(d > 0xffffffffu ? 0xffffffffu : d);
            }
            if (fwrite(row, sizeof(uint32_t), (size_t)reps, f) != (size_t)reps) {
                perror("fwrite"); return 2;
            }
        }
    }
    free(row);
    fclose(f);

    /* Hand the key to the caller exactly once. The caller hashes it into the
     * published verifier and deletes it; it is never committed. */
    FILE *sf = fopen(argv[3], "wb");
    if (!sf) { perror("fopen secret"); return 2; }
    if (fwrite(secret, 1, TAG_LEN, sf) != TAG_LEN) { perror("fwrite secret"); return 2; }
    fclose(sf);
    fprintf(stderr, "harness: wrote %s (%d x 256 x %ld uint32)\n",
            argv[2], TAG_LEN, reps);
    return 0;
}
