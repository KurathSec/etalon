#!/usr/bin/env python3
"""Regenerate the paper's figures from committed data.

The same discipline as bin/regen.py for numbers: a figure is a number nobody can
re-derive if it is drawn by hand, so every figure here is produced from the
committed results by this script, into paper/tches/fig/ (gitignored, like the
generated macros). Each figure carries one finding.

  fig-blindspot  dudect's max |t| per pair against its permutation null: the
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
import re
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
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
    label = {"_sentinel-positive": "sentinel", "ecdsa-nonce": "nonce,\nlatency",
             "ecdsa-address": "nonce,\naddress", "hqc-reject": "rejection",
             "kyberslash": "division"}
    seq = ["ecdsa-nonce", "ecdsa-address", "_sentinel-positive",
           "hqc-reject", "kyberslash"]
    # Plot the statistic the verdict actually rests on: dudect's max |t| against the
    # permutation null computed from each run's own committed samples. Every dump here
    # is taken at the same budget, so |t| is directly comparable across pairs and the
    # null band is one horizontal region; tau and its calibrated band are retired
    # (a fixed tau band is not budget-invariant under the null, see sec/method).
    perm = json.loads((REPO / "results" / "dudect_permutation.json").read_text())
    by = {(r["pair"], r["arm"]): r for r in perm["rows"]}
    vt = [by[(p, "vulnerable")]["observed_max_abs_t"] for p in seq]
    pt = [by[(p, "patched")]["observed_max_abs_t"] for p in seq]
    # The null band: the widest 95th percentile of any run's own permutation null, so a
    # bar clearing it clears every run's null, not just its own.
    thr = max(r["null_max_abs_t_p95"] for r in perm["rows"])
    names = [label[p] for p in seq]
    x = range(len(seq))

    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    ax.axhspan(1e-1, thr, color=LIGHT, zorder=0)
    ax.axhline(thr, color=MUTE, lw=0.9, ls="--", zorder=1)
    w = 0.38
    ax.bar([i - w / 2 for i in x], vt, w, color=TEAL, label="vulnerable arm", zorder=3)
    ax.bar([i + w / 2 for i in x], pt, w, color=MUTE, label="patched arm", zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(2e-1, 2000)
    ax.set_xticks(list(x))
    ax.set_xticklabels(names)
    ax.set_ylabel(r"dudect max $|t|$  (log)")
    ax.text(len(seq) - 1, thr * 2.6, "detected", color=INK, fontsize=7.5, ha="center")
    ax.text(len(seq) - 1, thr * 0.32, "permutation null", color=WARM, fontsize=7.5,
            ha="center")
    ax.annotate("missed:\nboth inside the null", xy=(4, vt[-1]), xytext=(3.3, thr * 14),
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


# The dividend interval the deployed KyberSlash division actually sees. After the
# conditional add the input t is in [0, KYBER_Q), so the dividend (t<<1) + KYBER_Q/2
# runs over [KYBER_Q/2, 2*KYBER_Q + KYBER_Q/2] = [1664, 8320] (pairs/kyberslash/src).
# The operand sweeps below run far wider, to characterise the divider; shading this
# band keeps the reader from reading a decade of the curve as the attack's range.
def kyber_q() -> int:
    """The modulus, read from the pair's own header rather than typed here."""
    hdr = (REPO / "pairs" / "kyberslash" / "src" / "kyber_slash.h").read_text()
    return int(re.search(r"#define\s+KYBER_Q\s+(\d+)", hdr).group(1))


KS_LO = kyber_q() // 2
KS_HI = (kyber_q() - 1) * 2 + kyber_q() // 2


def shade_kyber_range(ax, label=True):
    ax.axvspan(KS_LO, KS_HI, color=LIGHT, zorder=0)
    if label:
        ax.annotate("KyberSlash\noperands", xy=((KS_LO * KS_HI) ** 0.5, 1),
                    xycoords=("data", "axes fraction"), xytext=(0, -12),
                    textcoords="offset points", fontsize=6.8, color=WARM,
                    ha="center", va="top")


def fig_graviton():
    # Single clean panel: the per-udiv latency rising with dividend magnitude on the
    # Neoverse-V1 (a serial-dependency chain at a fixed dividend, so both classes run
    # identical code). This is the operand-magnitude dependence that carries F3. The
    # earlier right panel plotted a low-vs-high end-to-end percentage whose measurement
    # program generated the two classes with different constant reductions; that number
    # is confounded and pending re-measurement, so it is not plotted.
    g = json.loads((REPO / "results" / "kyberslash_graviton.json").read_text())
    lat = g["results"]["udiv_latency_operand_dependent"]["ticks_per_udiv"]
    xs = [1, 3000, 8000, 1e6, 4e9]
    ys = [lat["dividend_1"], lat["dividend_3000"], lat["dividend_8000"],
          lat["dividend_1e6"], lat["dividend_4e9"]]

    fig, a = plt.subplots(figsize=(4.6, 2.4))
    shade_kyber_range(a)
    a.plot(xs, ys, "-o", color=TEAL, ms=4, lw=1.4, zorder=3)
    a.set_xscale("log")
    a.set_xlabel("dividend magnitude")
    a.set_ylabel("ticks / udiv")
    a.set_title("Neoverse-V1 udiv latency rises with the operand", fontsize=8.5)
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
    shade_kyber_range(a)
    a.plot(xs, ys, "-o", color=TEAL, ms=4, lw=1.4, zorder=3)
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
    # What this figure has to show is not a level against a threshold but a SIGN that is
    # stable within an amplification and flips between amplifications, because that is
    # what tells a measurement-configuration artifact apart from an operand-dependent
    # divider. So plot the per-division mean difference of every repetition, signed, with
    # zero drawn: a real per-division step would sit on one side at every factor.
    d = json.loads((REPO / "results" / "kyberslash_detection_curve.json").read_text())
    curve = d["curve"]
    amps = [c["amp"] for c in curve]
    runs = d.get("runs", len(curve[0]["ticks_per_division_runs"]))

    fig, ax = plt.subplots(figsize=(5.2, 2.7))
    ax.axhline(0, color=INK, lw=1.0)
    for i, c in enumerate(curve):
        vals = c["ticks_per_division_runs"]
        xs = [i] * len(vals)
        consistent = c["mean_sign_positive_runs"] in (0, len(vals))
        ax.plot(xs, vals, "o", ms=5, color=(TEAL if consistent else MUTE),
                alpha=0.85, zorder=3)
        mean = sum(vals) / len(vals)
        ax.plot([i - 0.22, i + 0.22], [mean, mean], "-",
                color=(TEAL if consistent else MUTE), lw=2, zorder=4)
    ax.set_xticks(range(len(amps)))
    ax.set_xticklabels([str(a) for a in amps])
    ax.set_xlabel("amplification factor (divisions chained per measurement)")
    ax.set_ylabel("mean difference\n(ticks per division)")
    ax.set_title(f"the sign flips between factors: not the divider ({runs} runs each)",
                 fontsize=8.5)
    ax.text(0.99, 0.03,
            "filled = same sign in every run; grey = sign scattered",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color=MUTE)
    fig.savefig(FIG / "fig-detection-curve.pdf")
    plt.close(fig)


def fig_matrixssl_ladder():
    """The MatrixSSL fix, as four designs across three releases.

    Plots the class difference in ticks, NOT the test statistic. On the same-digit
    designs |t| sits above 200 on all three releases, indistinguishable, while the effect
    falls by a third: the statistic has saturated and only the quantity with units still
    moves. Plotting |t| here would hide the difference between releases entirely and would
    contradict this paper's own reporting rule.

    No fold-change is drawn between releases. Each bar is one of three acquisitions
    of that design from one retained build, and the between-acquisition range IS
    committed (results/matrixssl_repeats.json); what bars the ratio is that the
    releases are separately BUILT arms, not that spread is unmeasured; the reader can see the fall without being handed a
    number the corpus cannot support.
    """
    doc = json.loads((REPO / "results" / "fix_verification.json").read_text())
    des = doc["libraries"]["matrixssl"]["measurements_full_report"]["designs"]
    versions = [("mx4-2-1", "4.2.1\npre-fix"), ("mx430", "4.3.0\nfixed"),
                ("mx4-6-0", "4.6.0\nlatest")]
    rows = [("same", "same length\n256 v 256"), ("bit255v256", "one leading zero\n255 v 256"),
            ("samedigit", "same digit count\n193 v 256"), ("diffdigit", "digit count differs\n192 v 256")]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    width, colours, FLOOR = 0.26, [WARM, TEAL, MUTE], 0.7
    for vi, (vkey, vlab) in enumerate(versions):
        xs, ys, los, his, nz = [], [], [], [], []
        for ri, (rkey, _) in enumerate(rows):
            d = des.get(f"{vkey}_{rkey}")
            if not d:
                ax.text(ri + (vi - 1) * width, 1.4, "not\nrun", ha="center", va="bottom",
                        fontsize=6, color=MUTE, linespacing=0.9)
                continue
            e = abs(d["effect_ticks"])
            xs.append(ri + (vi - 1) * width)
            ys.append(max(e, 1.0))
            los.append(max(e - abs(d["ci_low"] - d["effect_ticks"]), FLOOR))
            his.append(e + abs(d["ci_high"] - d["effect_ticks"]))
            nz.append(bool(d["ci_excludes_zero"]))
        # A bar whose interval straddles zero is drawn open. On a log axis of
        # |effect| a null looks like a small positive effect, because the sign is
        # gone and the lower bound cannot reach the origin; the same-length controls
        # would read as a real 30-tick difference. Open bars say what they are.
        for x, y, keep in zip(xs, ys, nz):
            ax.bar([x], [y], width * 0.9,
                   color=colours[vi] if keep else "none",
                   edgecolor=colours[vi] if keep else MUTE,
                   linewidth=0 if keep else 0.8, linestyle="solid" if keep else "dashed")
        ax.errorbar(xs, ys, yerr=[[y - l for y, l in zip(ys, los)],
                                  [h - y for y, h in zip(ys, his)]],
                    fmt="none", ecolor=INK, elinewidth=0.7, capsize=2)
    ax.set_yscale("log")
    ax.set_ylabel("class difference (ticks)")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels([lab for _, lab in rows], fontsize=7, linespacing=1.1)
    ax.axhline(1.0, color=MUTE, lw=0.6, ls=":")
    # Empty bar containers do not carry a colour into the legend, so build the proxies.
    handles = [mpatches.Patch(facecolor=c, edgecolor="none", label=l.replace("\n", " "))
               for c, (_, l) in zip(colours, versions)]
    handles.append(mpatches.Patch(facecolor="none", edgecolor=MUTE, linewidth=0.8,
                                  linestyle="dashed", label="interval includes zero"))
    ax.legend(handles=handles, frameon=False, fontsize=7, ncol=2, loc="upper left")
    ax.set_ylim(0.7, 4e6)
    fig.savefig(FIG / "fig-matrixssl-ladder.pdf")
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_blindspot()
    fig_emission()
    fig_graviton()
    fig_x86_idiv()
    fig_detection_curve()
    fig_matrixssl_ladder()
    print(f"figures: wrote {len(list(FIG.glob('*.pdf')))} to {FIG}")


if __name__ == "__main__":
    main()
