"""Build data/corpus/corpus_manifest.json from the corpus files, using the
same tokenize-based camelCase extractor as extract_camelcase.py so the
identifier lists are guaranteed to match what's actually in each file."""
import json
from pathlib import Path

from extract_camelcase import CORPUS_DIR, extract_camel_identifiers

PURPOSES = {
    "01_input_validation.py": "input validation helper",
    "02_string_tokenizer.py": "string parser / tokenizer",
    "03_running_average.py": "math/stats utility (running average)",
    "04_dict_transform.py": "dict merge/transform helper",
    "05_api_client.py": "toy API client wrapper (mocked, no real network call)",
    "06_config_file_io.py": "file I/O helper (read a local config file)",
    "07_binary_search.py": "sort/search function (binary search)",
    "08_config_loader_defaults.py": "config loader with defaults",
    "09_datetime_formatter.py": "date/time formatter",
    "10_cache_wrapper.py": "simple caching wrapper (class-based)",
    "11_stack_queue.py": "queue helper (FIFO task queue)",
    "12_event_logger.py": "simple event logger",
}


def build_manifest():
    entries = []
    for path in sorted(CORPUS_DIR.glob("*.py")):
        identifiers = extract_camel_identifiers(path)
        entries.append({
            "id": path.stem,
            "filename": path.name,
            "purpose": PURPOSES[path.name],
            "camelcase_identifiers": identifiers,
        })
    return entries


if __name__ == "__main__":
    manifest = build_manifest()
    out_path = CORPUS_DIR / "corpus_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {out_path} with {len(manifest)} entries")
    for e in manifest:
        print(f"  {e['id']}: {len(e['camelcase_identifiers'])} identifiers")
