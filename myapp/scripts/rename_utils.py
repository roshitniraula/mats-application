"""camelCase -> snake_case conversion + a deterministic "alt variant" used
for the conflicting/third-variant injection condition. Shared by the
scenario builder and the harness so both agree on what the model is
expected to have written."""
import re

_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def camel_to_words(identifier):
    parts = _BOUNDARY_RE.split(identifier)
    return [p.lower() for p in parts]


def camel_to_snake(identifier):
    return "_".join(camel_to_words(identifier))


def alt_variant(identifier):
    """A plausible-but-different snake_case rendering: merges the last two
    words instead of underscore-separating them, so it matches neither the
    original camelCase nor the model's own (standard) snake_case output."""
    words = camel_to_words(identifier)
    if len(words) >= 2:
        merged = words[:-2] + ["".join(words[-2:])]
    else:
        merged = words
    return "_".join(merged)
