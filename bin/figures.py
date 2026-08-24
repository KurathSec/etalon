#!/usr/bin/env python3
"""Regenerate the paper's figures from committed data.

The same discipline as bin/regen.py for numbers: a figure is a number nobody can
re-derive if it is drawn by hand, so every figure here is produced from the
committed results by this script, into paper/tches/fig/ (gitignored, like the
generated macros). Each figure carries one finding.

  fig-blindspot  dudect's t-statistic per pair: the nonce leaks tower, the
                 division sits at the noise floor. The blind spot, quantified.
  fig-emission   the KyberSlash division emitted per (compiler, optimisation)
                 cell: two of eight, and the compilers disagree. The label is
                 not a property of source.
  fig-graviton   the udiv latency against operand magnitude on Graviton3, and the
                 step at the divisor boundary. The leak's magnitude is
                 microarchitecture-dependent.

Usage: bin/figures.py
"""
from __future__ import annotations

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
FIG = REPO / "paper" / "tches" / "fig"

INK = "#1c2b2d"
TEAL = "#0f6e6e"
WARM = "#b4531f"
MUTE = "#9aa7a7"
LIGHT = "#e7eded"

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def fig_blindspot():
    rows = [r for r in read_jsonl(REPO / "results" / "verdicts.jsonl")
            if r.get("tool") == "dudect" and r.get("applicable")]
    label = {"_sentinel-positive": "sentinel", "ecdsa-nonce": "nonce,\nlatency",
             "ecdsa-address": "nonce,\naddress", "hqc-reject": "rejection",
             "kyberslash": "division"}
    order = ["ecdsa-nonce", "ecdsa-address", "sentinel_marker",
             "hqc-reject", "kyberslash"]
    rows = {r["pair"]: r for r in rows}
    seq = ["ecdsa-nonce", "ecdsa-address", "_sentinel-positive",
           "hqc-reject", "kyberslash"]
    # Plot tau (dudect's budget-invariant effect size), the PR-3 decision variable,
    # against the null band calibrated on the negative sentinel, not the retired
    # [10,500] band on the raw t.
    thr = json.loads((REPO / "results" / "dudect_calibration.json").read_text())["null_threshold_tau"]
    vt = [rows[p]["vulnerable_max_tau"] for p in seq]
    pt = [rows[p]["patched_max_tau"] for p in seq]
    names = [label[p] for p in seq]
    x = range(len(seq))

    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    ax.axhspan(1e-3, thr, color=LIGHT, zorder=0)
    ax.axhline(thr, color=MUTE, lw=0.9, ls="--", zorder=1)
    w = 0.38
    ax.bar([i - w / 2 for i in x], vt, w, color=TEAL, label="vulnerable arm", zorder=3)
    ax.bar([i + w / 2 for i in x], pt, w, color=MUTE, label="patched arm", zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(2e-3, 300)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel(r"dudect $\tau = |t|/\sqrt{n}$  (log)")
    ax.text(len(seq) - 1, thr * 2.4, "leak", color=INK, fontsize=7.5, ha="center")
    ax.text(len(seq) - 1, thr * 0.35, "null band", color=WARM, fontsize=7.5, ha="center")
    ax.annotate("missed:\nboth in null band", xy=(4, vt[-1]), xytext=(3.3, thr * 12),
                fontsize=7.5, color=WARM, ha="center",
                arrowprops=dict(arrowstyle="->", color=WARM, lw=0.8))
    ax.legend(frameon=False, fontsize=7.5, loc="upper right",
              bbox_to_anchor=(1.0, 1.02))
    fig.savefig(FIG / "fig-blindspot.pdf")
    plt.close(fig)


def fig_emission():
    cells = json.loads((REPO / "results" / "kyberslash_emission.json")
                       .read_text())["emission_map"]
    vendors = ["gcc", "clang"]
    opts = ["O0", "O2", "O3", "Os"]
    grid = {(c["vendor"], c["opt"]): c for c in cells}

    fig, ax = plt.subplots(figsize=(4.2, 2.0))
    for r, v in enumerate(vendors):
        for col, o in enumerate(opts):
            c = grid[(v, o)]
            leaks = c["leak_emitted"]
            ax.add_patch(plt.Rectangle((col, r), 1, 1, facecolor=(WARM if leaks else LIGHT),
                                       edgecolor="white", lw=2))
            ax.text(col + 0.5, r + 0.5, ("idiv" if leaks else "reciprocal"),
                    ha="center", va="center", fontsize=(8.5 if leaks else 7),
                    color=("white" if leaks else MUTE),
                    fontweight=("bold" if leaks else "normal"))
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 2)
    ax.set_xticks([i + 0.5 for i in range(4)])
    ax.set_xticklabels(opts)
    ax.set_yticks([0.5, 1.5])
    ax.set_yticklabels(vendors)
    ax.set_xlabel("optimisation level")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    fig.savefig(FIG / "fig-emission.pdf")
    plt.close(fig)


def fig_graviton():
    g = json.loads((REPO / "results" / "kyberslash_graviton.json").read_text())
    lat = g["results"]["udiv_latency_operand_dependent"]["ticks_per_udiv"]
    e2e = g["results"]["end_to_end_coeff_to_bit_Os"]
    xs = [1, 3000, 8000, 1e6, 4e9]
    ys = [lat["dividend_1"], lat["dividend_3000"], lat["dividend_8000"],
          lat["dividend_1e6"], lat["dividend_4e9"]]

    fig, (a, b) = plt.subplots(1, 2, figsize=(5.6, 2.5),
                               gridspec_kw={"width_ratios": [1.35, 1]})
    a.plot(xs, ys, "-o", color=TEAL, ms=4, lw=1.4)
    a.set_xscale("log")
    a.set_xlabel("dividend magnitude")
    a.set_ylabel("ticks / udiv")
    a.set_title("latency rises with the operand", fontsize=8.5)

    # Right: the end-to-end operand-magnitude leak, low- vs high-coefficient call
    # time (the 5.8% separation), not a single-coefficient boundary step.
    lo, hi = e2e["low_coeffs_ticks_per_call"], e2e["high_coeffs_ticks_per_call"]
    pct = e2e["delta_percent_of_call"]
    b.bar([0, 1], [lo, hi], width=0.6, color=[MUTE, WARM])
    b.set_xticks([0, 1])
    b.set_xticklabels(["low coeff\n(quot. 0)", "high coeff\n(quot. $\\geq$1)"], fontsize=8)
    b.set_ylim(min(lo, hi) - 0.25, max(lo, hi) + 0.25)
    b.set_ylabel("ticks / call")
    b.set_title("operand-magnitude leak", fontsize=8.5)
    b.annotate(f"{pct:.1f}\\%", xy=(1, hi), xytext=(0.35, hi + 0.08),
               fontsize=8, color=WARM, ha="center")
    fig.savefig(FIG / "fig-graviton.pdf")
    plt.close(fig)


def fig_x86_idiv():
    x = json.loads((REPO / "results" / "kyberslash_x86_idiv.json").read_text())["results"]
    lat = x["idiv_latency_operand_dependent"]["ticks_per_udiv"]
    step = x["kyberslash_operand_range_step"]
    xs = [1, 3000, 8000, 1e6, 4e9]
    ys = [lat["dividend_1"], lat["dividend_3000"], lat["dividend_8000"],
          lat["dividend_1e6"], lat["dividend_4e9"]]

    fig, (a, b) = plt.subplots(1, 2, figsize=(5.6, 2.5),
                               gridspec_kw={"width_ratios": [1.35, 1]})
    a.plot(xs, ys, "-o", color=TEAL, ms=4, lw=1.4)
    a.set_xscale("log")
    a.set_xlabel("dividend magnitude")
    a.set_ylabel("TSC ticks / div")
    a.set_title("per-div latency vs dividend", fontsize=8.5)

    # Right panel: the operand step at the KyberSlash boundary (coeff 832 -> 833) as
    # the robust paired-difference median, with the same-operand noise floor as its
    # error bar, against zero. Both quantities come from one interleaved paired loop,
    # so the figure and the paper macro report the same number; the step straddles
    # zero within noise, which is why dudect's clean verdict is correct on this host.
    signed_step = step["step_ticks"]
    noise = step["noise_floor_ticks"]
    b.axhline(0, color=MUTE, lw=0.8, ls="--")
    b.errorbar([0], [signed_step], yerr=noise, fmt="o", color=WARM, ms=6,
               ecolor=INK, elinewidth=1.2, capsize=5)
    b.set_xticks([0])
    b.set_xticklabels(["coeff 832 $\\to$ 833"], fontsize=8)
    b.set_xlim(-0.7, 0.7)
    lim = max(noise, abs(signed_step)) * 2.4
    b.set_ylim(-lim, lim)
    b.set_ylabel("paired step (TSC ticks)")
    b.set_title("no step: within noise of 0", fontsize=8.5)
    b.annotate(f"step {abs(signed_step):.3f}\n$\\pm$ noise {noise:.3f}", xy=(0, signed_step),
               xytext=(0.14, lim * 0.45), fontsize=7.5, color=INK, ha="left")
    fig.savefig(FIG / "fig-x86-idiv.pdf")
    plt.close(fig)


def fig_detection_curve():
    d = json.loads((REPO / "results" / "kyberslash_detection_curve.json").read_text())
    amps = [p["amp"] for p in d["curve"]]
    ts = [p["abs_t"] for p in d["curve"]]
    band = d.get("leak_band", 500)
    # the nonce leak's amplification and t, for contrast
    nonce_amp, nonce_t = 40, None
    for line in (REPO / "results" / "verdicts.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("tool") == "dudect" and r.get("pair") == "ecdsa-nonce":
            nonce_t = r.get("vulnerable_max_t")

    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    ax.plot(amps, ts, "-o", color=TEAL, ms=5, lw=1.5, label="KyberSlash division")
    ax.axhline(band, color=WARM, ls="--", lw=1.2)
    ax.text(amps[0], band * 1.2, f"dudect leak band ({band})", color=WARM, fontsize=7.5, va="bottom")
    if nonce_t:
        ax.plot([nonce_amp], [nonce_t], "s", color=INK, ms=7)
        ax.annotate(f"nonce leak\n{nonce_t:.0f} at {nonce_amp}$\\times$", xy=(nonce_amp, nonce_t),
                    xytext=(nonce_amp * 0.42, nonce_t * 0.5), fontsize=7.5, color=INK, ha="center")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("amplification factor")
    ax.set_ylabel("dudect $|t|$")
    ax.set_title("amplification does not surface the division", fontsize=8.5)
    ax.set_xticks(amps + [nonce_amp])
    ax.set_xticklabels([str(a) for a in amps] + [str(nonce_amp)], fontsize=7.5)
    fig.savefig(FIG / "fig-detection-curve.pdf")
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_blindspot()
    fig_emission()
    fig_graviton()
    fig_x86_idiv()
    fig_detection_curve()
    print(f"figures: wrote {len(list(FIG.glob('*.pdf')))} to {FIG}")


if __name__ == "__main__":
    main()
