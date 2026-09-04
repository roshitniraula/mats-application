"""
Three-scenario contrast at the pre-response fork (see run_probe.py for the
single-scenario version and full method writeup):

  s01 - conflicting/revert, clean non-notice (never registers the
        discrepancy even in thinking, per REPORT.md) - says "No".
  s05 - conflicting/revert, notices and correctly reasons "external
        process" in thinking, then says "No" anyway (Example 1a).
  s16 - orthogonal/docstring_append, notices and actually says "Yes".

Prediction being tested: if the pre-response-fork "Yes"-surge seen in s05 is
a real signal of internal noticing (not generic layer-23-31 noise), it
should track *noticing*, not *what was said* - i.e. s05 and s16 (both
notice internally) should show it; s01 (never notices) should not, even
though s01 and s05 both surface-level say "No".

Usage: source probe-env/bin/activate && python3 compare_scenarios.py
"""
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
)

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

YES_STRINGS = ["Yes", " Yes", "yes", " yes", "是的", "YES"]
NO_STRINGS = ["No", " No", "no", " no", "NO"]


def token_ids_for(tokenizer, strings):
    ids = set()
    for s in strings:
        enc = tokenizer.encode(s, add_special_tokens=False)
        if len(enc) == 1:
            ids.add(enc[0])
    return ids


def pre_response_position(tokenizer, full_text, tokens_len):
    think_close = full_text.rfind("</think>")
    after_marker = "</think>\n\n"
    content_start_char = think_close + len(after_marker)
    n_before_content = len(tokenizer.encode(full_text[:content_start_char]))
    return min(n_before_content - 1, tokens_len - 1)


def main():
    print("loading model...", flush=True)
    model, tokenizer = load_model()
    yes_ids = token_ids_for(tokenizer, YES_STRINGS)
    no_ids = token_ids_for(tokenizer, NO_STRINGS)
    print("yes token ids:", yes_ids, "no token ids:", no_ids, flush=True)

    scenarios = ["s01", "s05", "s16"]
    results = {}

    for sid in scenarios:
        record = load_scenario_record(sid)
        messages = build_messages_through_turn(record, upto="turn3", include_final_assistant=True)
        tokens, full_text = tokenize_messages(tokenizer, messages, add_generation_prompt=False)
        seq_len = tokens.shape[1]
        pos = pre_response_position(tokenizer, full_text, seq_len)

        activations, _ = run_captured_forward(model, tokens)
        n_layers = len(activations)

        per_layer = []
        for layer_idx in range(n_layers):
            resid = activations[layer_idx][pos : pos + 1, :]
            logits_row = logit_lens(model, resid)[0]
            logits_row = logits_row - mx.max(logits_row)
            probs = mx.exp(logits_row) / mx.sum(mx.exp(logits_row))
            yes_mass = float(sum(probs[i].item() for i in yes_ids))
            no_mass = float(sum(probs[i].item() for i in no_ids))
            per_layer.append({"layer": layer_idx, "yes_mass": yes_mass, "no_mass": no_mass})

        results[sid] = {
            "condition": record["condition"],
            "actual_first_word": record["turn3"]["content"][:20],
            "seq_len": seq_len,
            "pre_response_pos": pos,
            "per_layer": per_layer,
        }
        print(f"\n=== {sid} ({record['condition']}) actual first words: {record['turn3']['content'][:30]!r} ===")
        for row in per_layer:
            bar_y = "#" * int(row["yes_mass"] * 40)
            bar_n = "#" * int(row["no_mass"] * 40)
            print(f"  layer {row['layer']:2d}  yes={row['yes_mass']:.3f} {bar_y:<40} no={row['no_mass']:.3f} {bar_n}")

    out_path = RESULTS_DIR / "s01_s05_s16_comparison.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
