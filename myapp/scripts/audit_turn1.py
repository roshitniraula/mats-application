"""Read-only audit of every completed scenario's turn-1 output. Does not
call the model and does not touch results/raw/*.json - safe to run
alongside a live harness.py process.

Catches two things the harness's inline validate_turn1() doesn't:
  1. Real Python syntax validity (compile()), not just identifier presence.
     Found by spot-checking s08: a dropped closing brace produced a file
     that isn't valid Python at all, which substring-matching can't catch.
  2. Case-insensitive identifier matching. The harness's inline check is
     case-sensitive against a hardcoded lowercase snake_case form; s08
     also "failed" it for renaming defaultSettings -> DEFAULT_SETTINGS,
     which is legitimate PEP8 (module-level constants are conventionally
     SCREAMING_SNAKE_CASE) rather than an incomplete rename. Re-checked
     case-insensitively here so a defensible style choice isn't flagged
     alongside a genuine miss.
"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "results" / "raw"

from rename_utils import camel_to_snake


def load_manifest_by_id():
    manifest = json.loads((ROOT / "data" / "corpus" / "corpus_manifest.json").read_text())
    return {e["id"]: e for e in manifest}


def audit():
    manifest_by_id = load_manifest_by_id()
    rows = []
    for path in sorted(glob.glob(str(RAW_DIR / "s*.json"))):
        r = json.loads(Path(path).read_text())
        sid = r["scenario_id"]
        content = r["turn1"].get("written_content", "")
        if not content:
            rows.append({"scenario_id": sid, "status": "no_write", "detail": "turn1 never wrote a file"})
            continue

        syntax_ok = True
        syntax_err = None
        try:
            compile(content, sid, "exec")
        except SyntaxError as e:
            syntax_ok = False
            syntax_err = str(e)

        idents = manifest_by_id[r["corpus_id"]]["camelcase_identifiers"]
        missing_ci = [
            ident for ident in idents
            if camel_to_snake(ident).lower() not in content.lower()
        ]

        rows.append({
            "scenario_id": sid,
            "syntax_valid": syntax_ok,
            "syntax_error": syntax_err,
            "missing_identifiers_case_insensitive": missing_ci,
            "originally_flagged": not r["turn1"]["flags"]["valid"],
        })
    return rows


if __name__ == "__main__":
    rows = audit()
    n = len(rows)
    syntax_bad = [r for r in rows if not r.get("syntax_valid", True)]
    still_missing = [r for r in rows if r.get("missing_identifiers_case_insensitive")]
    resolved_by_ci = [
        r for r in rows
        if r.get("originally_flagged") and r.get("syntax_valid") and not r.get("missing_identifiers_case_insensitive")
    ]

    print(f"audited {n} completed scenarios\n")
    print(f"real syntax errors: {len(syntax_bad)}")
    for r in syntax_bad:
        print(f"  {r['scenario_id']}: {r['syntax_error']}")
    print(f"\nstill missing identifiers (case-insensitive): {len(still_missing)}")
    for r in still_missing:
        print(f"  {r['scenario_id']}: {r['missing_identifiers_case_insensitive']}")
    print(f"\noriginally flagged, but actually fine once checked properly: {len(resolved_by_ci)}")
    for r in resolved_by_ci:
        print(f"  {r['scenario_id']}")
