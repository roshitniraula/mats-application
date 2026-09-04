"""Shared style, palette, and data loading for scripts/generate_visuals.py.

Palette reuses the validated categorical slots from the Attribution Board
dashboard built earlier this session (Delta E checked against CVD/normal-
vision floors before use, not eyeballed) so the paper's static figures and
that interactive dashboard read as one consistent visual system rather
than two unrelated palettes."""
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
PROBING_ROOT = ROOT.parent / "Probing"

# --- palette (light-mode values from the validated reference palette) ---
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#898781"
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
HAIR = "#e1e0d9"
HAIR_STRONG = "#c3c2b7"

BLUE = "#2a78d6"      # categorical slot 1
ORANGE = "#eb6834"    # categorical slot 2
AQUA = "#1baf7a"       # categorical slot 3
YELLOW = "#c98500"     # categorical slot 4 (dark step, better contrast on white)
VIOLET = "#4a3aa7"     # categorical slot 7
VIOLET_SOFT = "#c3bce8"

GOOD = "#0ca30c"
CRITICAL = "#d03b3b"

CONDITION_COLOR = {
    "conflicting": BLUE,
    "orthogonal": ORANGE,
    "baseline": INK_3,
    "disclosure": AQUA,
}
CONDITION_LABEL = {
    "conflicting": "Conflicting",
    "orthogonal": "Orthogonal",
    "baseline": "Baseline",
    "disclosure": "Disclosure",
}

FONT_STACK = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


def apply_style():
    plt.rcParams.update({
        "font.family": FONT_STACK,
        "font.size": 11,
        "text.color": INK,
        "axes.edgecolor": HAIR_STRONG,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "axes.linewidth": 0.8,
        "xtick.color": INK_3,
        "ytick.color": INK_3,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "grid.color": HAIR,
        "grid.linewidth": 0.7,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "svg.fonttype": "none",
    })


def savefig(fig, name, dpi=200):
    out_dir = ROOT / "visuals"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=SURFACE)
    print(f"wrote {path}")


LABEL_VARS = ["noticed", "self_blame", "external_recognized", "vague_only", "false_claim", "disclosed"]
VAR_DISPLAY = {
    "noticed": "Noticed",
    "self_blame": "Self-blame",
    "external_recognized": "External\nrecognized",
    "vague_only": "Vague only",
    "false_claim": "False claim",
    "disclosed": "Disclosed",
}


def to_bool(v):
    return str(v).strip().lower() in ("1", "true", "yes", "t", "y")


def load_graded_data():
    """Same loader as compute_stats.py, duplicated here to keep this file
    standalone/runnable from the .viz-venv without cross-importing a
    module that itself has no third-party deps but lives alongside ones
    that do."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from read_xlsx import read_xlsx

    rows = read_xlsx(str(ROOT / "results" / "for_review.xlsx"))
    header = rows[0]
    ncols = len(header)
    idx = {c: header.index(c) for c in header}
    scenarios = {s["scenario_id"]: s for s in json.loads((ROOT / "data" / "scenarios.json").read_text())}

    out = []
    for r in rows[1:]:
        r = r + [""] * (ncols - len(r))
        sid = r[0].strip()
        if not sid:
            continue
        spec = scenarios.get(sid, {})
        entry = {
            "scenario_id": sid,
            "condition": r[idx["condition"]],
            "subtype": spec.get("injection", {}).get("type", "?"),
        }
        for turn in ("turn2", "turn3"):
            for v in LABEL_VARS:
                entry[f"{turn}_{v}"] = to_bool(r[idx[f"{turn}_{v}"]])
        out.append(entry)
    return out


def load_probe_data():
    path = PROBING_ROOT / "results" / "batch_yesmass.csv"
    with open(path) as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        out[(r["scenario_id"], r["turn"])] = r
    return out
