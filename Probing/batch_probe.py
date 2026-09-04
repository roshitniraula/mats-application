"""
Scales the pre-response-fork "yes-mass" measurement (see compare_scenarios.py
for the n=3 case study that motivated this) across all 42 non-excluded
scenarios (s08/s20/s32/s44 excluded - see myapp/results/anomalies_log.md),
for both turn 2 and turn 3. Fully label-free - doesn't need
results/for_review.csv grading to be finished, since it only reads the
already-collected raw transcripts (results/raw/*.json) and the model's own
weights. Purpose: once grading finishes, this computed signal
(peak internal "yes"-mass in layers 22-30, at the exact position where the
model is about to start its visible answer) can be correlated against the
hand labels (turn2_noticed, turn3_disclosed, etc.) as an external check on
whether it's tracking real internal noticing or just surface wording - see
STATUS.md for what to do with this once labels exist.

Writes results/batch_yesmass.csv, one row per (scenario, turn).

Usage: source probe-env/bin/activate && python3 batch_probe.py
"""
import csv
import json
from pathlib import Path

import mlx.core as mx

from probe_lib import (
    build_messages_through_turn,
    load_model,
    load_scenario_record,
    logit_lens,
    run_captured_forward,
    tokenize_messages,
    RAW_DIR,
)

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

YES_STRINGS = ["Yes", " Yes", "yes", " yes", "是的", "YES"]
NO_STRINGS = ["No", " No", "no", " no", "NO"]
PEAK_LAYER_RANGE = (18, 31)  # inclusive; covers the surge window seen in the n=3 case study


def token_ids_for(tokenizer, strings):
    ids = set()
    for s in strings:
        enc = tokenizer.encode(s, add_special_tokens=False)
        if len(enc) == 1:
            ids.add(enc[0])
    return ids


def pre_response_position(tokenizer, full_text, tokens_len):
    think_close = full_text.rfind("</think>")
    if think_close == -1:
        return None
    after_marker = "</think>\n\n"
    content_start_char = think_close + len(after_marker)
    n_before_content = len(tokenizer.encode(full_text[:content_start_char]))
    return min(n_before_content - 1, tokens_len - 1)


def probe_turn(model, tokenizer, record, upto, yes_ids, no_ids):
    """Returns per-layer yes/no mass at the pre-response fork for one turn,
    or None if that turn has no usable thinking/content (e.g. turn had a
    tool call as its only action, no text response - the fabricated
    injected-read rounds and the rare "model never produced text" cases)."""
    turn = record[upto]
    if not turn or not turn.get("content") or not turn.get("thinking"):
        return None

    messages = build_messages_through_turn(record, upto=upto, include_final_assistant=True)
    tokens, full_text = tokenize_messages(tokenizer, messages, add_generation_prompt=False)
    seq_len = tokens.shape[1]
    pos = pre_response_position(tokenizer, full_text, seq_len)
    if pos is None:
        return None

    activations, _ = run_captured_forward(model, tokens)
    n_layers = len(activations)

    per_layer_yes, per_layer_no = [], []
    for layer_idx in range(n_layers):
        resid = activations[layer_idx][pos : pos + 1, :]
        logits_row = logit_lens(model, resid)[0]
        logits_row = logits_row - mx.max(logits_row)
        probs = mx.exp(logits_row) / mx.sum(mx.exp(logits_row))
        per_layer_yes.append(float(sum(probs[i].item() for i in yes_ids)))
        per_layer_no.append(float(sum(probs[i].item() for i in no_ids)))

    lo, hi = PEAK_LAYER_RANGE
    peak_yes = max(per_layer_yes[lo : hi + 1])
    peak_no = max(per_layer_no[lo : hi + 1])
    final_yes = per_layer_yes[-1]
    final_no = per_layer_no[-1]

    return {
        "seq_len": seq_len,
        "peak_yes_mass": peak_yes,
        "peak_no_mass": peak_no,
        "final_yes_mass": final_yes,
        "final_no_mass": final_no,
        "per_layer_yes": per_layer_yes,
        "per_layer_no": per_layer_no,
    }


FIELDNAMES = [
    "scenario_id", "turn", "condition", "excluded", "actual_starts_with",
    "actual_first_40_chars", "seq_len", "peak_yes_mass", "peak_no_mass",
    "final_yes_mass", "final_no_mass",
]


def load_done_keys(csv_path):
    """(scenario_id, turn) pairs already present in an existing CSV, so a
    resumed run skips work instead of redoing it from scratch. This is what
    was missing the first time - an earlier full-batch run got killed
    partway through (at s28/46) to relieve severe memory pressure it was
    causing on a 16GB machine (unified memory shared with everything else
    running), and that run only wrote its CSV at the very end, so nothing
    was recoverable except by re-parsing the stdout log by hand. Doing this
    properly now so a future interruption doesn't cost the same rework."""
    if not csv_path.exists():
        return set()
    with open(csv_path) as f:
        return {(r["scenario_id"], r["turn"]) for r in csv.DictReader(f)}


def main():
    scenario_ids = sorted(p.stem for p in RAW_DIR.glob("s*.json"))
    print(f"{len(scenario_ids)} scenario files found", flush=True)

    csv_path = RESULTS_DIR / "batch_yesmass.csv"
    done = load_done_keys(csv_path)
    if done:
        print(f"resuming: {len(done)} (scenario, turn) rows already in {csv_path.name}", flush=True)

    write_header = not csv_path.exists()
    csv_file = open(csv_path, "a", newline="")
    writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
    if write_header:
        writer.writeheader()

    print("loading model...", flush=True)
    model, tokenizer = load_model()
    yes_ids = token_ids_for(tokenizer, YES_STRINGS)
    no_ids = token_ids_for(tokenizer, NO_STRINGS)

    n_rows = len(done)
    for i, sid in enumerate(scenario_ids):
        record = load_scenario_record(sid)
        excluded = sid in ("s08", "s20", "s32", "s44")
        for upto in ("turn2", "turn3"):
            if (sid, upto) in done:
                continue
            try:
                res = probe_turn(model, tokenizer, record, upto, yes_ids, no_ids)
            except Exception as e:
                print(f"  {sid}/{upto}: ERROR {e}", flush=True)
                continue
            finally:
                mx.clear_cache()  # release MLX's Metal buffer cache between turns - peak
                                   # unified-memory use is what caused the earlier interruption
            if res is None:
                print(f"  {sid}/{upto}: skipped (no text response, e.g. tool-call-only turn)", flush=True)
                continue
            content = record[upto]["content"].strip()
            starts_with = (
                "yes" if content[:4].lower().startswith("yes") else
                "no" if content[:3].lower().startswith("no") else
                "other"
            )
            row = {
                "scenario_id": sid,
                "turn": upto,
                "condition": record["condition"],
                "excluded": excluded,
                "actual_starts_with": starts_with,
                "actual_first_40_chars": content[:40],
                "seq_len": res["seq_len"],
                "peak_yes_mass": round(res["peak_yes_mass"], 4),
                "peak_no_mass": round(res["peak_no_mass"], 4),
                "final_yes_mass": round(res["final_yes_mass"], 4),
                "final_no_mass": round(res["final_no_mass"], 4),
            }
            writer.writerow(row)
            csv_file.flush()  # every row lands on disk immediately, not just at exit
            n_rows += 1
            print(f"  [{i+1}/{len(scenario_ids)}] {sid}/{upto} ({record['condition']}, says={starts_with}): "
                  f"peak_yes={row['peak_yes_mass']:.3f} peak_no={row['peak_no_mass']:.3f}", flush=True)

    csv_file.close()
    print(f"\ndone: {csv_path} has {n_rows} rows total")


if __name__ == "__main__":
    main()
