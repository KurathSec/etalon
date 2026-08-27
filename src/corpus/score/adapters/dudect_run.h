#ifndef DUDECT_RUN_H
#define DUDECT_RUN_H
/* Shared dudect run loop for every pair driver.
 *
 * Two changes from the original inline loop, both required by PR-3:
 *
 *  1. FULL BUDGET. The loop always runs DUDECT_RUN_BATCHES batches; it does not
 *     stop the moment dudect declares a leak. The original early stop meant that
 *     any recorded max t in the (10, 500) band was a first-crossing value under
 *     optional stopping, a lower bound, mislabelled "budget exhausted". Running
 *     to the full budget makes the final max t a real budget-exhausted reading.
 *
 *  2. RAW DUMP. When DUDECT_RAW_DUMP names a path, the per-measurement (class,
 *     exec_time) samples are written there, up to DUDECT_RAW_CAP records, so a
 *     bootstrap confidence interval over committed samples can re-decide the
 *     verdict without re-measuring. The first ten measurements of each batch are
 *     discarded, matching dudect's own warm-up discard.
 *
 * dudect still does the measurement and computes its own t (one "max t:" line
 * per batch, so the whole t-trajectory reaches the adapter). Only the decision
 * rule moves out: since PR-4 the verdict is a permutation test over the dumped
 * samples (bin/dudect_permute.py), with bin/dudect_ci.py reporting the effect
 * size beside it, not the verdict; the calibrated tau band is retired.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
/* NOTE: dudect.h is a single-header library with no include guard, so this file
 * must NOT include it again; the driver includes <dudect.h> (with
 * DUDECT_IMPLEMENTATION) before including this header, and the dudect types used
 * below are in scope from that include. */

#ifndef DUDECT_RUN_BATCHES
#define DUDECT_RUN_BATCHES 40
#endif
#ifndef DUDECT_RAW_CAP
#define DUDECT_RAW_CAP 400000
#endif

static int dudect_run_and_dump(dudect_config_t *config) {
  /* A uniform per-batch measurement count across pairs, set from the environment,
   * so batches x measurements is the same total budget everywhere and readings
   * are comparable across pairs. The verdict needs no cross-pair transfer: it is
   * decided against the PR-4 permutation null built from this run's own samples
   * within its batches (bin/dudect_permute.py), matched to the budget by
   * construction. */
  const char *ms = getenv("DUDECT_MEASUREMENTS");
  if (ms) { long v = atol(ms); if (v > 0) config->number_measurements = (size_t)v; }
  dudect_ctx_t ctx;
  dudect_init(&ctx, config);
  size_t M = config->number_measurements;
  const char *dump = getenv("DUDECT_RAW_DUMP");
  FILE *f = dump ? fopen(dump, "wb") : NULL;
  size_t written = 0;
  /* Batch count is env-tunable so the fixed budget can be matched to a pair's
   * per-measurement cost (an amplified or EC pair is far slower per call) without
   * recompiling; it is a fixed budget either way, never an early stop. */
  int batches = DUDECT_RUN_BATCHES;
  const char *bs = getenv("DUDECT_BATCHES");
  if (bs) { int v = atoi(bs); if (v > 0) batches = v; }
  dudect_state_t state = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
  /* Records written per batch. The dump has no header, and the permutation null
   * shuffles labels WITHIN each batch, so the block boundaries must be known
   * exactly: equal splits are right only when no delta was dropped, and a
   * dropped delta is what makes 56,968 out of 3 x 19,989. The adapter writes
   * these counts to a sidecar beside the dump. */
  size_t per_batch[64];
  dudect_state_t last = state;
  for (int b = 0; b < batches; b++) {
    size_t before = written;
    state = dudect_main(&ctx);           /* prints "max t: ..." each batch */
    if (f && written < (size_t)DUDECT_RAW_CAP) {
      for (size_t i = 10; i + 1 < M && written < (size_t)DUDECT_RAW_CAP; i++) {
        int64_t t = ctx.exec_times[i];
        if (t <= 0) continue;            /* drop non-positive deltas */
        uint8_t cl = ctx.classes[i];
        fwrite(&cl, 1, 1, f);
        fwrite(&t, sizeof(int64_t), 1, f);
        written++;
      }
    }
    if (b < 64) per_batch[b] = written - before;
    last = state;
  }
  if (f) fclose(f);
  (void)last;
  printf("DUDECT_BATCH_RECORDS");
  for (int b = 0; b < batches && b < 64; b++) printf(" %zu", per_batch[b]);
  printf("\n");
  dudect_free(&ctx);
  /* Exit code is never the verdict; the adapter keys on this line and on the
   * committed samples. */
  printf("DUDECT_VERDICT %s\n",
         state == DUDECT_LEAKAGE_FOUND ? "LEAK" : "NO_LEAK_EVIDENCE");
  return 0;
}
#endif
