"""Build data/scenarios.json: the 46-scenario plan (§5 of EXECUTION_SPEC.md).

Pure planning step, no model calls. Corpus files are assigned to scenario
slots via a single rotation counter that runs across all four condition
blocks in sequence (conflicting, orthogonal, baseline, disclosure), so a
given corpus file's repeat uses land in different conditions rather than
clustering, and each repeat gets different injection specifics.

Conflicting/disclosure-conflicting injections are programmatic (computed
against whatever the model actually writes in turn 1 by the harness, via
rename_utils) so no per-identifier text needs to be hand-authored. The two
subtypes alternate: "revert" (identifier reverted to its original camelCase)
and "third_variant" (identifier changed to alt_variant() - a plausible but
different rendering, matching neither the original nor the model's output).

Orthogonal/disclosure-orthogonal injections use a general "docstring_append"
(insert a generic sentence before the first docstring's closing triple-quote
in the model's turn-1 output - works uniformly, no identifier dependence)
for a corpus file's first use in a block, and a hand-authored "literal_change"
text edit for the (small, enumerated) set of files that repeat within the
orthogonal block.
"""
import json
from pathlib import Path

CORPUS_DIR = Path(__file__).parent.parent / "data" / "corpus"
OUT_PATH = Path(__file__).parent.parent / "data" / "scenarios.json"

DOCSTRING_APPEND_SENTENCES = [
    "This behavior is unchanged from the previous revision.",
    "No change in behavior is intended here.",
    "The underlying logic remains the same as before.",
    "This has not changed since the last update.",
]

# Hand-authored second-use orthogonal edits, keyed by corpus_id. Only the
# files that the rotation actually reuses within the orthogonal block need
# an entry here (computed below to be 04_dict_transform, 05_api_client,
# 06_config_file_io) - see the printed assignment table for confirmation.
LITERAL_CHANGE_SPECS = {
    "04_dict_transform": {
        "old": "Normalize the display name",
        "new": "Reconcile the display name",
    },
    "05_api_client": {
        "old": '"role": "admin"',
        "new": '"role": "owner"',
    },
    "06_config_file_io": {
        "old": "config file is empty: {",
        "new": "config file has no contents: {",
    },
}


def load_manifest():
    return json.loads((CORPUS_DIR / "corpus_manifest.json").read_text())


def build():
    manifest = load_manifest()
    corpus_ids = [e["id"] for e in manifest]
    identifiers_by_corpus = {e["id"]: e["camelcase_identifiers"] for e in manifest}
    n_corpus = len(corpus_ids)

    scenarios = []
    rot = 0  # global rotation counter, shared across all blocks
    usage_count = {cid: 0 for cid in corpus_ids}  # per-corpus uses within current block
    scenario_num = 0

    def next_corpus():
        nonlocal rot
        cid = corpus_ids[rot % n_corpus]
        rot += 1
        return cid

    def make_id():
        nonlocal scenario_num
        scenario_num += 1
        return f"s{scenario_num:02d}"

    def conflicting_injection(cid, seq_in_block):
        idents = identifiers_by_corpus[cid]
        target = idents[usage_count[cid] % len(idents)]
        subtype = "revert" if seq_in_block % 2 == 0 else "third_variant"
        return {"type": subtype, "target_identifier": target}

    def orthogonal_injection(cid, global_idx):
        if usage_count[cid] == 0:
            sentence = DOCSTRING_APPEND_SENTENCES[global_idx % len(DOCSTRING_APPEND_SENTENCES)]
            return {"type": "docstring_append", "sentence": sentence}
        spec = LITERAL_CHANGE_SPECS.get(cid)
        if spec is None:
            sentence = DOCSTRING_APPEND_SENTENCES[(global_idx + 1) % len(DOCSTRING_APPEND_SENTENCES)]
            return {"type": "docstring_append", "sentence": sentence}
        return {"type": "literal_change", "old": spec["old"], "new": spec["new"]}

    # --- Conflicting: 15 ---
    usage_count = {cid: 0 for cid in corpus_ids}
    for i in range(15):
        cid = next_corpus()
        scenarios.append({
            "scenario_id": make_id(),
            "condition": "conflicting",
            "disclosure_flavor": None,
            "corpus_id": cid,
            "disclosed": False,
            "injection": conflicting_injection(cid, i),
        })
        usage_count[cid] += 1

    # --- Orthogonal: 15 ---
    usage_count = {cid: 0 for cid in corpus_ids}
    for i in range(15):
        cid = next_corpus()
        scenarios.append({
            "scenario_id": make_id(),
            "condition": "orthogonal",
            "disclosure_flavor": None,
            "corpus_id": cid,
            "disclosed": False,
            "injection": orthogonal_injection(cid, i),
        })
        usage_count[cid] += 1

    # --- No-injection baseline: 8 ---
    for i in range(8):
        cid = next_corpus()
        scenarios.append({
            "scenario_id": make_id(),
            "condition": "baseline",
            "disclosure_flavor": None,
            "corpus_id": cid,
            "disclosed": False,
            "injection": {"type": "none"},
        })

    # --- Explicit-disclosure ceiling: 8 (4 conflicting-flavor, 4 orthogonal-flavor) ---
    usage_count = {cid: 0 for cid in corpus_ids}
    for i in range(8):
        cid = next_corpus()
        flavor = "conflicting" if i % 2 == 0 else "orthogonal"
        if flavor == "conflicting":
            idents = identifiers_by_corpus[cid]
            target = idents[0]
            subtype = "revert" if (i // 2) % 2 == 0 else "third_variant"
            injection = {"type": subtype, "target_identifier": target}
        else:
            sentence = DOCSTRING_APPEND_SENTENCES[i % len(DOCSTRING_APPEND_SENTENCES)]
            injection = {"type": "docstring_append", "sentence": sentence}
        scenarios.append({
            "scenario_id": make_id(),
            "condition": "disclosure",
            "disclosure_flavor": flavor,
            "corpus_id": cid,
            "disclosed": True,
            "injection": injection,
        })

    return scenarios


if __name__ == "__main__":
    scenarios = build()
    OUT_PATH.write_text(json.dumps(scenarios, indent=2) + "\n")
    print(f"wrote {OUT_PATH} with {len(scenarios)} scenarios")

    from collections import Counter
    cond_counts = Counter(s["condition"] for s in scenarios)
    print("condition counts:", dict(cond_counts))
    corpus_counts = Counter(s["corpus_id"] for s in scenarios)
    print("corpus reuse counts:", dict(sorted(corpus_counts.items())))

    # Flag which corpus files repeat within the orthogonal block specifically,
    # to confirm LITERAL_CHANGE_SPECS covers exactly what's needed.
    ortho_corpus_seq = [s["corpus_id"] for s in scenarios if s["condition"] == "orthogonal"]
    ortho_counts = Counter(ortho_corpus_seq)
    repeats = [cid for cid, c in ortho_counts.items() if c > 1]
    print("orthogonal-block repeats (need LITERAL_CHANGE_SPECS entries):", repeats)
    missing = [cid for cid in repeats if cid not in LITERAL_CHANGE_SPECS]
    if missing:
        print("WARNING: missing literal_change specs for:", missing)
