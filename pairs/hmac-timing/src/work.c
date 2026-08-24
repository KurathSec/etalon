#include "tag.h"

/* Deliberately opaque to the optimiser: the accumulator is volatile so the loop
 * cannot be folded away, which would silently remove the timing signal and turn
 * this control into one that passes by doing nothing. */
uint32_t byte_work(uint8_t a, uint8_t b)
{
    volatile uint32_t acc = 0;
    for (int i = 0; i < 1200; i++) {
        acc += (uint32_t)a * 2654435761u + (uint32_t)b;
        acc ^= acc >> 7;
    }
    return acc;
}
