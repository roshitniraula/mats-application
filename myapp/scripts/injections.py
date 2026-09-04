"""Turn the abstract injection specs from data/scenarios.json into an actual
manipulated file-content string, applied against the model's real turn-1
write_file content (so injections react to what the model actually wrote,
not to an assumption about it)."""
import re

from rename_utils import alt_variant, camel_to_snake


def apply_injection(injection, written_content):
    itype = injection["type"]

    if itype == "none":
        return written_content, {"applied": True, "method": "no_change"}

    if itype in ("revert", "third_variant"):
        identifier = injection["target_identifier"]
        snake = camel_to_snake(identifier)
        replacement = identifier if itype == "revert" else alt_variant(identifier)
        # IGNORECASE: a model that renames a module-level constant to
        # SCREAMING_SNAKE_CASE (legitimate PEP8, e.g. defaultSettings ->
        # DEFAULT_SETTINGS) still needs to be matched here - found via s08,
        # where a case-sensitive match against the lowercase form silently
        # produced a no-op injection (injection_meta: {"applied": false}),
        # meaning the "conflicting" condition's manipulation never actually
        # reached the model. See results/anomalies_log.md.
        pattern = re.compile(r"\b" + re.escape(snake) + r"\b", re.IGNORECASE)
        new_content, n = pattern.subn(replacement, written_content)
        return new_content, {
            "applied": n > 0,
            "occurrences_replaced": n,
            "from": snake,
            "to": replacement,
        }

    if itype == "docstring_append":
        marker = '\n    """'
        idx = written_content.find(marker)
        if idx == -1:
            new_content = written_content + f"\n# {injection['sentence']}\n"
            return new_content, {"applied": True, "method": "fallback_trailing_comment"}
        insertion = f"\n\n    {injection['sentence']}"
        new_content = written_content[:idx] + insertion + written_content[idx:]
        return new_content, {"applied": True, "method": "docstring_insert"}

    if itype == "literal_change":
        old, new = injection["old"], injection["new"]
        if old not in written_content:
            return written_content, {"applied": False, "reason": "old substring not found"}
        new_content = written_content.replace(old, new, 1)
        return new_content, {"applied": True}

    raise ValueError(f"unknown injection type: {itype}")
