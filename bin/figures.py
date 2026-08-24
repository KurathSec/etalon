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
    vt = [rows[p]["vulnerable_max_t"] for p in seq]
    pt = [rows[p]["patched_max_t"] for p in seq]
    names = [label[p] for p in seq]
    x = range(len(seq))

    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    ax.axhspan(10, 500, color=LIGHT, zorder=0)
    ax.axhline(500, color=MUTE, lw=0.8, ls="--", zorder=1)
    ax.axhline(10, color=MUTE, lw=0.8, ls="--", zorder=1)
    w = 0.38
    ax.bar([i - w / 2 for i in x], vt, w, color=TEAL, label="vulnerable arm", zorder=3)
    ax.bar([i + w / 2 for i in x], pt, w, color=MUTE, label="patched arm", zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(0.8, 60000)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel(r"dudect max $|t|$  (log)")
    ax.text(len(seq) - 1, 700, "detect", color=INK, fontsize=7.5, ha="center")
    ax.text(len(seq) - 1, 3.0, "no evidence", color=WARM, fontsize=7.5, ha="center")
    ax.annotate("missed:\nsame as patched", xy=(4, vt[-1]), xytext=(3.3, 40),
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
    step = g["results"]["kyberslash_operand_range_step"]
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

    lo, hi = step["coeff_below_833_ticks"], step["coeff_at_or_above_833_ticks"]
    b.bar([0, 1], [lo, hi], width=0.6, color=[MUTE, WARM])
    b.set_xticks([0, 1])
    b.set_xticklabels(["coeff\n< 833", "coeff\n$\\geq$ 833"], fontsize=8)
    b.set_ylim(2.3, 2.95)
    b.set_ylabel("ticks / call")
    b.set_title("the KyberSlash step", fontsize=8.5)
    b.annotate(f"+{step['step_ticks']:.3f}\nticks", xy=(1, hi), xytext=(0.3, 2.9),
               fontsize=7.5, color=WARM, ha="center")
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
    a.set_title("latency is flat in the operand", fontsize=8.5)

    lo, hi = step["coeff_below_833_ticks"], step["coeff_at_or_above_833_ticks"]
    noise = step["noise_floor_ticks"]
    mid = (lo + hi) / 2
    b.bar([0, 1], [lo, hi], width=0.6, color=[MUTE, WARM])
    # the noise floor as an error band around the pair mean, to show the step is inside it
    b.errorbar([0, 1], [mid, mid], yerr=noise, fmt="none", ecolor=INK,
               elinewidth=1.1, capsize=4)
    b.set_xticks([0, 1])
    b.set_xticklabels(["coeff\n< 833", "coeff\n$\\geq$ 833"], fontsize=8)
    b.set_ylim(mid - max(noise, abs(hi - lo)) * 2.2, mid + max(noise, abs(hi - lo)) * 2.2)
    b.set_ylabel("TSC ticks / div")
    b.set_title("no step: within noise", fontsize=8.5)
    b.annotate(f"step {abs(hi - lo):.3f}\n< noise {noise:.2f}", xy=(0.5, mid),
               xytext=(0.5, mid + noise * 1.1), fontsize=7.5, color=INK, ha="center")
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
