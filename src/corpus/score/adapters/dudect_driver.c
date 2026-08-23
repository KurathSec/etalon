/* dudect driver for the tag-comparison pairs.
 *
 * Two-class fixed-vs-random test on check_tag: class 0 always feeds a candidate
 * equal to the secret's prefix, class 1 feeds a random candidate. If the
 * comparison is not constant time, the two classes have different timing
 * distributions and dudect reports leakage.
 *
 * The arm under test is chosen by ARM_SOURCE at compile time, so the identical
 * driver scores the vulnerable and the patched build and any difference in
 * verdict is a property of the arm, not of the driver.
 */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include <string.h>
#include "tag.h"

/* The arm's check_tag is linked in separately. */
int check_tag(const uint8_t *secret, const uint8_t *candidate);

#define SECRET_LEN TAG_LEN
static uint8_t secret[SECRET_LEN];
static int secret_ready = 0;

void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes) {
  if (!secret_ready) { randombytes(secret, SECRET_LEN); secret_ready = 1; }
  for (size_t i = 0; i < c->number_measurements; i++) {
    classes[i] = randombit();
    uint8_t *cand = input_data + (size_t)i * c->chunk_size;
    if (classes[i] == 0) {
      /* class 0: a candidate sharing a long prefix with the secret */
      memcpy(cand, secret, SECRET_LEN);
      cand[SECRET_LEN - 1] ^= 1;      /* differ only in the last byte */
    } else {
      randombytes(cand, SECRET_LEN);  /* class 1: unrelated */
    }
  }
}

uint8_t do_one_computation(uint8_t *data) {
  return (uint8_t)check_tag(secret, data);
}

int main(void) {
  dudect_config_t config = {
    .chunk_size = SECRET_LEN,
    .number_measurements = 1e5,
  };
  dudect_ctx_t ctx;
  dudect_init(&ctx, &config);
  dudect_state_t state = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  /* Bounded number of batches so the adapter always terminates. */
  for (int i = 0; i < 40 && state == DUDECT_NO_LEAKAGE_EVIDENCE_YET; i++) {
    state = dudect_main(&ctx);
  }
  dudect_free(&ctx);
  /* Exit code is NOT the verdict; the adapter parses stdout. Print a machine
   * line the adapter keys on. */
  printf("DUDECT_VERDICT %s\n",
         state == DUDECT_LEAKAGE_FOUND ? "LEAK" : "NO_LEAK_EVIDENCE");
  return 0;
}
