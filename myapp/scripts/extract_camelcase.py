"""One-off helper: extract camelCase identifiers from each corpus file via
tokenize (not regex-over-text) so string/comment contents are ignored, and
print counts so we can sanity-check the 4-6-per-file target before writing
corpus_manifest.json by hand."""
import keyword
import re
import tokenize
from pathlib import Path

CORPUS_DIR = Path(__file__).parent.parent / "data" / "corpus"
CAMEL_RE = re.compile(r"^[a-z][a-zA-Z0-9]*$")


def extract_camel_identifiers(file_path):
    identifiers = []
    seen = set()
    with open(file_path, "rb") as f:
        for tok in tokenize.tokenize(f.readline):
            if tok.type != tokenize.NAME:
                continue
            name = tok.string
            if keyword.iskeyword(name) or name in seen:
                continue
            if not CAMEL_RE.match(name):
                continue
            if not any(c.isupper() for c in name):
                continue
            identifiers.append(name)
            seen.add(name)
    return identifiers


if __name__ == "__main__":
    for path in sorted(CORPUS_DIR.glob("*.py")):
        idents = extract_camel_identifiers(path)
        print(f"{path.name}: ({len(idents)}) {idents}")
