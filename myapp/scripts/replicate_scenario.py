"""Re-run one scenario's exact spec as an independent replication, kept
separate from the official 46 (results/replication/, never results/raw/) so
it can never silently inflate N. Built for the s08 anomaly (see
results/anomalies_log.md) - do NOT run this while the main `harness.py
--all` batch is still in progress, since both would compete for the same
local Ollama instance and slow each other down for no benefit. Run only
after the full 46-scenario run has completed.

Usage:
    python3 replicate_scenario.py s08
    python3 replicate_scenario.py s08 --label check2   # second replication
"""
import argparse
import json
import sys
import time
from pathlib import Path

from harness import load_manifest_by_id, load_scenarios, run_scenario

ROOT = Path(__file__).parent.parent
REPL_DIR = ROOT / "results" / "replication"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario_id", help="scenario id to replicate, e.g. s08")
    parser.add_argument("--label", default="replicate1", help="suffix for the output filename")
    args = parser.parse_args()

    scenarios = load_scenarios()
    matches = [s for s in scenarios if s["scenario_id"] == args.scenario_id]
    if not matches:
        print(f"no scenario {args.scenario_id} in data/scenarios.json", file=sys.stderr)
        sys.exit(1)
    spec = matches[0]

    original_path = ROOT / "results" / "raw" / f"{args.scenario_id}.json"
    if not original_path.exists():
        print(f"warning: original {original_path} not found - nothing to compare against", file=sys.stderr)

    REPL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPL_DIR / f"{args.scenario_id}_{args.label}.json"

    print(f"replicating {args.scenario_id} (same spec: {json.dumps(spec['injection'])}, "
          f"corpus={spec['corpus_id']}, disclosed={spec['disclosed']}) -> {out_path}")

    manifest_by_id = load_manifest_by_id()
    start = time.time()
    record = run_scenario(spec, manifest_by_id)
    elapsed = time.time() - start

    record["_replication_of"] = args.scenario_id
    out_path.write_text(json.dumps(record, indent=2) + "\n")

    if original_path.exists():
        original = json.loads(original_path.read_text())
        same_content = original["turn1"]["written_content"] == record["turn1"]["written_content"]
        print(f"done in {elapsed:.1f}s. turn1.written_content identical to original "
              f"(seed={record['generation_params'].get('seed')}): {same_content}")
        if not same_content:
            print("-> seed did NOT produce identical output; confirms the reproducibility "
                  "caveat in report/REPORT.md's limitations.")
    else:
        print(f"done in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
