"""Preliminary analysis of in-progress grading, read directly from
results/for_review.xlsx (the user's working copy, saved mid-grading to
prevent data loss in the IDE). Read-only - does not touch for_review.csv
or the xlsx. Cross-references data/scenarios.json for injection subtype
(revert vs third_variant), which for_review's own columns don't carry."""
import json
from collections import defaultdict
from pathlib import Path

from read_xlsx import read_xlsx

ROOT = Path(__file__).parent.parent
XLSX_PATH = ROOT / "results" / "for_review.xlsx"

LABEL_VARS = ["noticed", "self_blame", "external_recognized", "vague_only", "false_claim", "disclosed"]
LABEL_COLS = [f"turn2_{v}" for v in LABEL_VARS] + [f"turn3_{v}" for v in LABEL_VARS]


def to_bool(val):
    v = val.strip().lower()
    if v in ("1", "true", "yes", "t", "y"):
        return True
    if v in ("0", "false", "no", "f", "n", ""):
        return False
    return None  # unrecognized, don't silently coerce


def load_graded_rows():
    rows = read_xlsx(str(XLSX_PATH))
    header = rows[0]
    ncols = len(header)
    idx = {c: header.index(c) for c in ["scenario_id", "condition", "corpus_id"] + LABEL_COLS}

    scenarios = {s["scenario_id"]: s for s in json.loads((ROOT / "data" / "scenarios.json").read_text())}

    graded = []
    for r in rows[1:]:
        r = r + [""] * (ncols - len(r))
        sid = r[0].strip()
        if not sid:
            continue
        filled = [c for c in LABEL_COLS if r[idx[c]].strip() != ""]
        if len(filled) != len(LABEL_COLS):
            continue  # not fully graded yet, skip

        spec = scenarios.get(sid, {})
        injection = spec.get("injection", {})
        subtype = injection.get("type", "?")

        entry = {"scenario_id": sid, "condition": r[idx["condition"]], "subtype": subtype}
        for c in LABEL_COLS:
            entry[c] = to_bool(r[idx[c]])
        graded.append(entry)
    return graded


def group_key(entry):
    cond = entry["condition"]
    sub = entry["subtype"]
    if cond == "conflicting":
        return f"conflicting/{sub}"
    if cond == "orthogonal":
        return "orthogonal"
    if cond == "baseline":
        return "baseline"
    if cond == "disclosure":
        return "disclosure"
    return cond


def main():
    graded = load_graded_rows()
    print(f"=== {len(graded)} scenarios fully graded so far ===\n")

    groups = defaultdict(list)
    for e in graded:
        groups[group_key(e)].append(e)

    for key in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        entries = groups[key]
        n = len(entries)
        print(f"--- {key} (n={n}) ---")
        for turn in ("turn2", "turn3"):
            counts = {v: sum(1 for e in entries if e[f"{turn}_{v}"]) for v in LABEL_VARS}
            print(f"  {turn}: " + ", ".join(f"{v}={counts[v]}/{n}" for v in LABEL_VARS))
        print()

    print("=== scenario ids included ===")
    for key in sorted(groups):
        print(f"  {key}: {[e['scenario_id'] for e in groups[key]]}")


if __name__ == "__main__":
    main()
