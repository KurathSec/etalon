/* dudect driver for KyberSlash's coeff_to_bit.
 *
 * Two-class fixed-vs-random over the secret coefficient. dudect measures whether
 * the reduction's timing depends on its operand. On a build that emits a
 * data-dependent division this leaks; on one that emits a reciprocal multiply it
 * does not. The chunk is two bytes, one uint16 coefficient in [0, KYBER_Q).
 */
#define DUDECT_IMPLEMENTATION
#include <dudect.h>
#include "dudect_run.h"
#include <string.h>
#include "kyber_slash.h"

uint16_t coeff_to_bit(uint16_t t);

void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes) {
  for (size_t i = 0; i < c->number_measurements; i++) {
    classes[i] = randombit();
    uint16_t v;
    if (classes[i] == 0) {
      v = 0;                        /* class 0: a fixed coefficient */
    } else {
      uint8_t r[2]; randombytes(r, 2);
      v = ((uint16_t)r[0] | ((uint16_t)r[1] << 8)) % KYBER_Q;  /* class 1: random */
    }
    memcpy(input_data + (size_t)i * c->chunk_size, &v, 2);
  }
}

uint8_t do_one_computation(uint8_t *data) {
  uint16_t v; memcpy(&v, data, 2);
  return (uint8_t)coeff_to_bit(v);
}

int main(void) {
  dudect_config_t config = { .chunk_size = 2, .number_measurements = 1e5 };
  return dudect_run_and_dump(&config);
}
