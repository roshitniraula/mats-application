"""Generates all figures for the paper into myapp/visuals/. Run with the
isolated venv that has matplotlib (this project's other scripts are
stdlib-only by design; matplotlib is scoped to this one visualization
task, not a project-wide dependency):

    scripts/.viz-venv/bin/python3 scripts/generate_visuals.py

Four figures, each chosen to carry a distinct, load-bearing part of the
paper's argument rather than restating a table. Cut after a first-draft
review: the full 42x12 classification heatmap (redundant with the
Results tables and unreadable at a glance) and the revert-vs-third-variant
secondary split (already fully tabulated in Results, and the weakest,
most caveated finding in the study - not worth a fifth chart's worth of
reader attention). What's left:
  1. headline_turn_gap    - the study's strongest result
  2. primary_comparison   - why the planned primary test wasn't significant
  3. activation_probe     - independent mechanistic corroboration
  4. reference_rates      - false-positive floor & best-case ceiling
  5. sample_flow          - accounting for how the 42 scenarios feed 1-4
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Patch

sys.path.insert(0, str(Path(__file__).parent))
from compute_stats import fisher_exact_2x2
from visuals_lib import (
    CONDITION_COLOR, CONDITION_LABEL, CRITICAL, GOOD, HAIR, HAIR_STRONG, INK,
    INK_2, INK_3, SURFACE, VAR_DISPLAY, VIOLET, VIOLET_SOFT, apply_style,
    load_graded_data, load_probe_data, savefig,
)


def fmt_p(p):
    return "p < 0.0001" if p < 0.0001 else f"p = {p:.4f}"


# ---------------------------------------------------------------------------
def fig1_headline_turn_gap(data):
    variables = ["noticed", "external_recognized", "disclosed"]
    n = len(data)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))

    y_positions = list(range(len(variables)))[::-1]
    for y, var in zip(y_positions, variables):
        t2 = sum(1 for e in data if e[f"turn2_{var}"]) / n * 100
        t3 = sum(1 for e in data if e[f"turn3_{var}"]) / n * 100

        ax.plot([t2, t3], [y, y], color=HAIR_STRONG, lw=2.2, zorder=1, solid_capstyle="round")
        ax.scatter([t2], [y], s=115, color=VIOLET_SOFT, edgecolor=VIOLET, linewidth=1.3, zorder=3)
        ax.scatter([t3], [y], s=115, color=VIOLET, edgecolor=VIOLET, linewidth=1.3, zorder=3)

        ax.text(t2, y + 0.28, f"{t2:.0f}%", ha="center", va="bottom", fontsize=9, color=INK_2)
        ax.text(t3, y - 0.32, f"{t3:.0f}%", ha="center", va="top", fontsize=9, color=INK_2, fontweight="bold")

    ax.set_yticks(y_positions)
    ax.set_yticklabels([VAR_DISPLAY[v].replace("\n", " ") for v in variables], fontsize=11)
    ax.set_xlim(-2, 108)
    ax.set_ylim(-0.7, len(variables) - 0.3)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    ax.scatter([], [], s=115, color=VIOLET_SOFT, edgecolor=VIOLET, linewidth=1.3, label="Spontaneous")
    ax.scatter([], [], s=115, color=VIOLET, edgecolor=VIOLET, linewidth=1.3, label="Forced")
    ax.legend(loc="lower right", bbox_to_anchor=(0.78, -0.32), ncol=2, fontsize=9.5)

    fig.suptitle(f"Model Disclosure Across Turns (N={n})", ha="center", fontsize=13, fontweight="bold")
    fig.subplots_adjust(top=0.86)
    savefig(fig, "01_headline_turn_gap.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig2_primary_comparison(data):
    """Grouped bars with a significance bracket over each pair (standard
    stats-figure convention) instead of a floating row of p-values - each
    p sits directly above the two bars it describes, at a height set by
    that pair's own values, so there's nothing to trace across the figure
    to connect a number to a bar."""
    variables = ["noticed", "external_recognized"]
    turns = ["turn2", "turn3"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.0), sharey=True)

    for ax, turn in zip(axes, turns):
        x = np.arange(len(variables))
        width = 0.32
        bar_vals = {}
        for i, cond in enumerate(["conflicting", "orthogonal"]):
            entries = [e for e in data if e["condition"] == cond]
            vals = [sum(1 for e in entries if e[f"{turn}_{v}"]) for v in variables]
            bar_vals[cond] = vals
            offset = (i - 0.5) * width
            bars = ax.bar(x + offset, vals, width, color=CONDITION_COLOR[cond],
                           label=CONDITION_LABEL[cond], edgecolor=SURFACE, linewidth=0.8, zorder=3)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.0f}", ha="center", fontsize=9, color=INK_2)

        for j, var in enumerate(variables):
            conf = [e for e in data if e["condition"] == "conflicting"]
            orth = [e for e in data if e["condition"] == "orthogonal"]
            a = sum(1 for e in conf if e[f"{turn}_{var}"]); b_ = len(conf) - a
            c = sum(1 for e in orth if e[f"{turn}_{var}"]); d = len(orth) - c
            p = fisher_exact_2x2([[a, b_], [c, d]])
            top = max(bar_vals["conflicting"][j], bar_vals["orthogonal"][j])
            y0, y1 = top + 1.2, top + 1.7
            x0, x1 = j - width / 2, j + width / 2
            ax.plot([x0, x0, x1, x1], [y0, y1, y1, y0], color=INK_3, linewidth=1.0, zorder=2)
            ax.text(j, y1 + 0.2, fmt_p(p), ha="center", va="bottom", fontsize=8.7, color=INK_2)

        ax.set_xticks(x)
        ax.set_xticklabels([VAR_DISPLAY[v].replace("\n", " ") for v in variables], fontsize=10.5)
        ax.set_ylim(0, 16)
        ax.set_yticks(range(0, 15, 2))
        ax.set_title("Turn 2 (Spontaneous)" if turn == "turn2" else "Turn 3 (Forced)", fontsize=11.5, pad=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", zorder=0)
        ax.set_axisbelow(True)

    n_conf = len([e for e in data if e["condition"] == "conflicting"])
    n_orth = len([e for e in data if e["condition"] == "orthogonal"])
    axes[0].set_ylabel("Number of scenarios")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.96), ncol=2, fontsize=9.5, frameon=False)
    fig.suptitle(f"Noticing and attribution by condition (n={n_conf} vs. n={n_orth})", x=0.02, y=1.05, ha="left", fontsize=13)
    fig.subplots_adjust(top=0.7, wspace=0.12)
    savefig(fig, "02_primary_comparison.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig3_activation_probe(data):
    """Raw dots, not aggregated bars - the story lives in individual
    points at n=4 vs n=10, and aggregating would hide that 2 of the 4
    truly-noticed cases sit near the missed-it cluster rather than
    claiming a clean separation that isn't there."""
    probe = load_probe_data()
    denied = []
    for e in data:
        if e["turn3_disclosed"]:
            continue
        key = (e["scenario_id"], "turn3")
        if key in probe:
            denied.append({"noticed": e["turn3_noticed"], "yes_mass": float(probe[key]["peak_yes_mass"])})

    true_vals = sorted(r["yes_mass"] for r in denied if r["noticed"])
    false_vals = sorted(r["yes_mass"] for r in denied if not r["noticed"])

    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    rng = np.random.default_rng(42)

    rows = [(false_vals, INK_3, "Genuinely missed it"),
            (true_vals, VIOLET, "Noticed it, denied anyway")]
    for y, (vals, color, _) in enumerate(rows):
        jitter = rng.uniform(-0.15, 0.15, size=len(vals))
        ax.scatter(vals, [y + j for j in jitter], s=100, color=color, alpha=0.9,
                   edgecolor=SURFACE, linewidth=1.0, zorder=3)

    ax.axvline(0.5, color=HAIR_STRONG, linewidth=1.1, linestyle=(0, (4, 3)), zorder=1)

    x0, x1 = 1.1, 1.14
    ax.plot([x0, x1, x1, x0], [0, 0, 1, 1], color=INK_3, linewidth=1.0, zorder=2, clip_on=False)
    ax.text(x1 + 0.015, 0.5, "p = 0.004", ha="left", va="center", fontsize=9.5, color=INK_2, clip_on=False)

    ax.set_yticks([0, 1])
    ax.set_yticklabels([r[2] for r in rows], fontsize=10.5)
    ax.set_xlim(-0.05, 1.08)
    ax.set_ylim(-0.55, 1.95)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("Peak internal “Yes” signal confidence by outcome", labelpad=9, fontsize=10)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", zorder=0)
    ax.set_axisbelow(True)

    fig.suptitle(f"Logit Lens Probing (n={len(true_vals)} vs. n={len(false_vals)})", ha="center", fontsize=13, fontweight="bold")
    fig.subplots_adjust(top=0.85, right=0.86)
    savefig(fig, "03_activation_probe.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig4_reference_rates(data):
    fig, ax = plt.subplots(figsize=(6.8, 3.5))
    base = [e for e in data if e["condition"] == "baseline"]
    disc = [e for e in data if e["condition"] == "disclosure"]

    groups = [
        ("Baseline\n(no change made)", base, lambda e: e["turn2_noticed"] or e["turn2_false_claim"],
         lambda e: e["turn3_noticed"] or e["turn3_false_claim"], CRITICAL),
        ("Disclosure\n(told exactly what changed)", disc, lambda e: e["turn2_external_recognized"] or e["turn2_disclosed"],
         lambda e: e["turn3_external_recognized"] or e["turn3_disclosed"], GOOD),
    ]

    x = np.arange(2)
    width = 0.32
    for gi, (glabel, entries, f2, f3, color) in enumerate(groups):
        n_total = len(entries)
        c2 = sum(1 for e in entries if f2(e))
        c3 = sum(1 for e in entries if f3(e))
        v2, v3 = c2 / n_total * 100, c3 / n_total * 100
        b1 = ax.bar(gi - width / 2, v2, width, color=color, alpha=0.45, edgecolor=color, linewidth=1.2)
        b2 = ax.bar(gi + width / 2, v3, width, color=color, alpha=1.0, edgecolor=color, linewidth=1.2)
        for b, c, v in [(b1, c2, v2), (b2, c3, v3)]:
            ax.text(b[0].get_x() + b[0].get_width() / 2, v + 3, f"n = {c}/{n_total} ({v:.0f}%)",
                    ha="center", fontsize=8.7, color=INK_2)

    ax.set_xticks(x)
    ax.set_xticklabels([g[0] for g in groups], fontsize=10.5)
    ax.set_ylim(0, 125)
    ax.set_ylabel("% of scenarios")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", zorder=0)
    ax.set_axisbelow(True)
    # neutral proxies: color already encodes baseline/disclosure, so the
    # legend should only decode the alpha (turn 2 vs turn 3), not repeat
    # a hue that doesn't match both groups' bars
    legend_handles = [
        Patch(facecolor=INK_3, alpha=0.45, edgecolor=INK_3, label="Turn 2"),
        Patch(facecolor=INK_3, alpha=1.0, edgecolor=INK_3, label="Turn 3"),
    ]
    ax.legend(handles=legend_handles, loc="upper center", ncol=2, fontsize=9.5)
    ax.set_title(f"False-positive rate vs. disclosure ceiling (n={len(base)} each)", loc="left", fontsize=13)
    savefig(fig, "04_reference_rates.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
def fig5_sample_flow(data, probe):
    """Box-and-arrow accounting of how the 42 valid scenarios feed each of
    figures 1-4 - added after review flagged that four charts each honestly
    reporting their own n still doesn't show a reader how those n's relate
    to one another or to the full sample."""

    def box(ax, cx, cy, w, h, text, face, edge, fontsize=9.5, weight="normal"):
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                     boxstyle="round,pad=0.02,rounding_size=0.08",
                                     facecolor=face, edgecolor=edge, linewidth=1.3, zorder=3))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, color=INK, weight=weight, zorder=4)

    def arrow(ax, start, end, color=HAIR_STRONG, style="-", lw=1.3):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color=color, linewidth=lw, linestyle=style,
                                     shrinkA=0, shrinkB=0, mutation_scale=14), zorder=2)

    conditions = ["conflicting", "orthogonal", "baseline", "disclosure"]
    cond_n = {c: sum(1 for e in data if e["condition"] == c) for c in conditions}

    not_disclosed = [e for e in data if not e["turn3_disclosed"] and (e["scenario_id"], "turn3") in probe]
    nd_by_cond = {c: sum(1 for e in not_disclosed if e["condition"] == c) for c in conditions}
    n_noticed = sum(1 for e in not_disclosed if e["turn3_noticed"])
    n_missed = sum(1 for e in not_disclosed if not e["turn3_noticed"])

    fig, ax = plt.subplots(figsize=(11, 7.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    root_xy = (6, 9.3)
    box(ax, *root_xy, 4.4, 0.85, f"42 valid scenarios", HAIR, INK_3, fontsize=10.5, weight="bold")

    fig1_xy = (10.6, 9.3)
    box(ax, *fig1_xy, 2.4, 0.85, "Fig 1\n(all 42)", SURFACE, VIOLET, fontsize=9)
    arrow(ax, (root_xy[0] + 2.2, root_xy[1]), (fig1_xy[0] - 1.2, fig1_xy[1]))

    cond_x = {"conflicting": 1.4, "orthogonal": 4.2, "baseline": 7.0, "disclosure": 9.6}
    cond_y = 7.4
    for c in conditions:
        box(ax, cond_x[c], cond_y, 2.3, 0.85,
            f"{CONDITION_LABEL[c]}\n(n={cond_n[c]})", SURFACE, CONDITION_COLOR[c])
        arrow(ax, (root_xy[0], root_xy[1] - 0.43), (cond_x[c], cond_y + 0.43))

    fig2_xy = (2.8, 5.3)
    box(ax, *fig2_xy, 3.6, 0.95, f"Fig 2\nConflicting vs. Orthogonal (n=28)", SURFACE, VIOLET, fontsize=9)
    for c in ["conflicting", "orthogonal"]:
        arrow(ax, (cond_x[c], cond_y - 0.43), (fig2_xy[0] + (cond_x[c] - fig2_xy[0]) * 0.15, fig2_xy[1] + 0.475))

    fig4_xy = (8.3, 5.3)
    box(ax, *fig4_xy, 3.6, 0.95, f"Fig 4\nBaseline vs. Disclosure (n=14)", SURFACE, VIOLET, fontsize=9)
    for c in ["baseline", "disclosure"]:
        arrow(ax, (cond_x[c], cond_y - 0.43), (fig4_xy[0] + (cond_x[c] - fig4_xy[0]) * 0.15, fig4_xy[1] + 0.475))

    nd_xy = (5.5, 3.1)
    box(ax, *nd_xy, 5.6, 1.05,
        f"Not disclosed at turn 3 (n={len(not_disclosed)})\n"
        f"Baseline {nd_by_cond['baseline']} · Conflicting {nd_by_cond['conflicting']} · Orthogonal {nd_by_cond['orthogonal']}",
        "#fdf6ec", "#c98500", fontsize=8.7)
    arrow(ax, (nd_xy[0], root_xy[1] - 0.43), (nd_xy[0], nd_xy[1] + 0.53),
          color=HAIR_STRONG, style=(0, (4, 3)))

    noticed_xy = (3.9, 1.0)
    missed_xy = (7.1, 1.0)
    box(ax, *noticed_xy, 3.2, 0.9, f"Noticed, denied\n(n={n_noticed})", SURFACE, VIOLET, fontsize=9)
    box(ax, *missed_xy, 3.2, 0.9, f"Genuinely missed\n(n={n_missed})", SURFACE, INK_3, fontsize=9)
    arrow(ax, (nd_xy[0] - 0.6, nd_xy[1] - 0.53), (noticed_xy[0], noticed_xy[1] + 0.45))
    arrow(ax, (nd_xy[0] + 0.6, nd_xy[1] - 0.53), (missed_xy[0], missed_xy[1] + 0.45))
    ax.text(5.5, 0.15, "Fig 3", ha="center", va="center", fontsize=9, color=INK_2, style="italic")

    fig.suptitle("Sample Flow Across the Four Figures", ha="center", fontsize=13, fontweight="bold", y=0.98)
    savefig(fig, "05_sample_flow.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
def main():
    apply_style()
    data = load_graded_data()
    assert len(data) == 42, f"expected 42 graded scenarios, got {len(data)}"
    probe = load_probe_data()

    fig1_headline_turn_gap(data)
    fig2_primary_comparison(data)
    fig3_activation_probe(data)
    fig4_reference_rates(data)
    fig5_sample_flow(data, probe)
    print("\nAll 5 figures written to visuals/.")


if __name__ == "__main__":
    main()
