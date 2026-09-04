"""
Cross-references the label-free internal signal (results/batch_yesmass.csv -
peak "yes"-family probability mass at the pre-response fork, see
compare_scenarios.py / STATUS.md for the method and the n=3 case study that
motivated it) against Roshit's hand grading in
myapp/results/for_review.csv, once that grading is done.

Read-only against myapp/ - never writes there.

The real test this was built for (see STATUS.md, "What the batch run is
for", step 2): among scenarios where the *visible response* denies noticing
anything (turn{2,3}_disclosed == FALSE), does peak_yes_mass separate
turn{2,3}_noticed == TRUE from == FALSE? If yes, that's independent
validation - from inside the model, not from reading its stated CoT - of
exactly the gap REPORT.md's Example 1a (s05) already flagged as the
single most important transcript collected. If no, that's also a real,
honestly-reportable result (this exploratory technique didn't generalize),
not a failure to hide.

Safe to run before grading is finished - it just reports on however many
rows currently have non-blank labels, and says plainly how many that is.

Usage: python3 validate_against_labels.py
(no MLX/model needed - pure CSV analysis, run with plain system python3 or
the probe-env, either works)
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent
MYAPP = ROOT.parent / "myapp"
FOR_REVIEW_CSV = MYAPP / "results" / "for_review.csv"
FOR_REVIEW_XLSX = MYAPP / "results" / "for_review.xlsx"
YESMASS = ROOT / "results" / "batch_yesmass.csv"


def load_labels():
    """Grading moved from CSV to Excel mid-session (Roshit graded in
    for_review.xlsx) - read whichever exists, xlsx preferred since it's the
    live one. Read-only, via openpyxl (installed into probe-env, not
    system/myapp)."""
    if FOR_REVIEW_XLSX.exists():
        import openpyxl
        wb = openpyxl.load_workbook(FOR_REVIEW_XLSX, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(rows_iter)]
        out = {}
        for raw in rows_iter:
            row = dict(zip(header, raw))
            sid = row.get("scenario_id")
            if not sid:
                continue
            # normalize all values to strings, like csv.DictReader would give us
            out[str(sid).strip()] = {k: ("" if v is None else str(v)) for k, v in row.items()}
        return out
    with open(FOR_REVIEW_CSV) as f:
        return {r["scenario_id"]: r for r in csv.DictReader(f)}


def load_yesmass():
    if not YESMASS.exists():
        return {}
    with open(YESMASS) as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        out[(r["scenario_id"], r["turn"])] = r
    return out


def as_bool(s):
    s = (s or "").strip().upper()
    if s in ("TRUE", "1", "T", "Y", "YES"):
        return True
    if s in ("FALSE", "0", "F", "N", "NO"):
        return False
    return None  # blank / not yet graded


def main():
    labels = load_labels()
    yesmass = load_yesmass()
    if not yesmass:
        print(f"{YESMASS} doesn't exist yet - batch probe hasn't produced results. Nothing to validate.")
        return

    print(f"{len(yesmass)} (scenario, turn) probe rows available.")

    checked = {"turn2": 0, "turn3": 0}
    graded = {"turn2": 0, "turn3": 0}
    rows_by_turn = {"turn2": [], "turn3": []}

    for (sid, turn), probe_row in yesmass.items():
        label_row = labels.get(sid)
        if label_row is None:
            continue
        checked[turn] += 1
        noticed = as_bool(label_row.get(f"{turn}_noticed"))
        disclosed = as_bool(label_row.get(f"{turn}_disclosed"))
        if noticed is None or disclosed is None:
            continue  # not graded yet
        graded[turn] += 1
        rows_by_turn[turn].append({
            "scenario_id": sid,
            "noticed": noticed,
            "disclosed": disclosed,
            "peak_yes_mass": float(probe_row["peak_yes_mass"]),
            "condition": probe_row["condition"],
        })

    for turn in ("turn2", "turn3"):
        print(f"\n=== {turn}: {graded[turn]}/{checked[turn]} probed scenarios have real labels ===")
        rows = rows_by_turn[turn]
        if len(rows) < 4:
            print("  not enough graded rows yet for a meaningful comparison - come back once grading progresses further.")
            continue

        # The key test: among "denied it" scenarios (disclosed=False), does
        # peak_yes_mass separate noticed=True from noticed=False?
        denied = [r for r in rows if not r["disclosed"]]
        noticed_denied = [r["peak_yes_mass"] for r in denied if r["noticed"]]
        not_noticed_denied = [r["peak_yes_mass"] for r in denied if not r["noticed"]]

        print(f"  Among {len(denied)} scenarios where the visible response did NOT disclose anything:")
        if noticed_denied:
            avg = sum(noticed_denied) / len(noticed_denied)
            print(f"    noticed=TRUE  (n={len(noticed_denied)}): mean peak_yes_mass = {avg:.3f}  {sorted(round(x,3) for x in noticed_denied)}")
        else:
            print("    noticed=TRUE  (n=0): no cases yet")
        if not_noticed_denied:
            avg = sum(not_noticed_denied) / len(not_noticed_denied)
            print(f"    noticed=FALSE (n={len(not_noticed_denied)}): mean peak_yes_mass = {avg:.3f}  {sorted(round(x,3) for x in not_noticed_denied)}")
        else:
            print("    noticed=FALSE (n=0): no cases yet")

        if noticed_denied and not_noticed_denied:
            gap = (sum(noticed_denied) / len(noticed_denied)) - (sum(not_noticed_denied) / len(not_noticed_denied))
            print(f"    gap (noticed - not_noticed, both denied): {gap:+.3f}")
            print("    (this is the number that matters - a real positive gap here is the actual finding;"
                  " small n means don't over-read a single run, but it's the right first check)")


if __name__ == "__main__":
    main()
