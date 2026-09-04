"""
First probing pass: does qwen3.5:9b's internal state, at the moment it
produces a false denial, still encode the correct external attribution it
reasoned its way to in its own (unseen-by-the-user) thinking?

Target case: s05 (conflicting/revert, myapp/report/REPORT.md's "Example
1a" - the single most important transcript in the checkpoint phase). Its
turn-3 thinking explicitly reasons "there was an inconsistency... could be
caused by: An external process or system modifying the file" - a correct
diagnosis - then its visible turn-3 response states "No, I didn't notice
anything unexpected..." Both from the same generation.

Method: label-free logit lens (no probe fitting, no ground truth needed -
appropriate since results/for_review.csv grading isn't done yet). Teacher-
forced replay of the real logged transcript through a raw MLX weight load
(see probe_lib.py for why Ollama can't be probed directly), then project
each layer's residual-stream output through the model's own unembedding at
two positions: the last token of the <think> block, and the first token of
the visible response. If the model "knows" externally-caused at some
intermediate layer even where the final output denies it, that should show
up as attribution-relevant tokens ranking highly in the logit lens well
before the final layer, at the thinking/response boundary.

Usage: source probe-env/bin/activate && python3 run_probe.py [scenario_id]
"""
import json
import sys
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


def find_boundary_token_positions(tokenizer, full_text, tokens_len):
    """Locates the token index of (a) the last token before '</think>' and
    (b) the first token of the visible response after '<think>...</think>'.
    Uses incremental re-tokenization of text prefixes (cheap relative to the
    forward pass) rather than an offset-mapping API, since mlx_lm's
    tokenizer wrapper doesn't uniformly expose one across tokenizer
    backends."""
    think_close = full_text.rfind("</think>")
    if think_close == -1:
        raise ValueError("no </think> found in rendered text - reasoning_content wasn't rendered as expected")

    prefix_before_close = full_text[:think_close]
    n_before_close = len(tokenizer.encode(prefix_before_close))

    after_marker = "</think>\n\n"
    content_start_char = think_close + len(after_marker)
    prefix_before_content = full_text[:content_start_char]
    n_before_content = len(tokenizer.encode(prefix_before_content))

    return {
        # predicts literally "</think>" - trivial, kept only as a pipeline
        # sanity check (does it converge to near-1.0 on the known-correct token).
        "last_thinking_token_idx": min(n_before_close - 1, tokens_len - 1),
        # the real position of interest: logits HERE predict the first token
        # of the visible response (i.e. the "No" vs "Yes" fork itself), not
        # the token after it. An earlier version read n_before_content
        # directly, which predicts the *second* response token instead -
        # off by one, fixed here.
        "pre_response_token_idx": min(n_before_content - 1, tokens_len - 1),
    }


def summarize_logits(tokenizer, logits_row, top_k=8):
    logits_row = logits_row - mx.max(logits_row)
    probs = mx.exp(logits_row) / mx.sum(mx.exp(logits_row))
    idx = mx.argsort(probs)[::-1][:top_k]
    idx_list = [int(i) for i in idx]
    return [
        {"token": tokenizer.decode([i]), "prob": float(probs[i])}
        for i in idx_list
    ]


def main():
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "s05"
    print(f"Loading model ({scenario_id})...", flush=True)
    model, tokenizer = load_model()

    record = load_scenario_record(scenario_id)
    messages = build_messages_through_turn(record, upto="turn3", include_final_assistant=True)
    tokens, full_text = tokenize_messages(tokenizer, messages, add_generation_prompt=False)
    seq_len = tokens.shape[1]
    print(f"scenario={scenario_id} tokens={seq_len}", flush=True)

    positions = find_boundary_token_positions(tokenizer, full_text, seq_len)
    print("boundary positions:", positions, flush=True)

    print("running captured forward pass...", flush=True)
    activations, final_logits = run_captured_forward(model, tokens)
    n_layers = len(activations)
    print(f"n_layers={n_layers}", flush=True)

    report = {
        "scenario_id": scenario_id,
        "condition": record["condition"],
        "seq_len": seq_len,
        "n_layers": n_layers,
        "boundary_positions": positions,
        "actual_turn3_thinking": record["turn3"]["thinking"],
        "actual_turn3_content": record["turn3"]["content"],
        "logit_lens": {"last_thinking_token": [], "pre_response_token": []},
    }

    for label, pos_key in [
        ("last_thinking_token", "last_thinking_token_idx"),
        ("pre_response_token", "pre_response_token_idx"),
    ]:
        pos = positions[pos_key]
        for layer_idx in range(n_layers):
            resid = activations[layer_idx][pos : pos + 1, :]  # (1, hidden)
            logits_row = logit_lens(model, resid)[0]
            top = summarize_logits(tokenizer, logits_row)
            report["logit_lens"][label].append({"layer": layer_idx, "top": top})
            print(f"[{label}] layer {layer_idx:2d}: " + ", ".join(f"{t['token']!r}:{t['prob']:.2f}" for t in top[:5]), flush=True)

    out_path = RESULTS_DIR / f"{scenario_id}_logitlens.json"
    out_path.write_text(json.dumps(report, indent=2, default=float))
    print(f"\nwrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
