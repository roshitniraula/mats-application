def validateUserInput(rawInput, maxLength=100):
    """Validate a raw user-supplied string and return a cleaned version.

    Strips whitespace, enforces a max length, and rejects a small set of
    characters that shouldn't appear in a plain text field.
    """
    if rawInput is None:
        raise ValueError("input cannot be None")

    trimmedValue = rawInput.strip()

    if len(trimmedValue) == 0:
        raise ValueError("input cannot be empty after trimming")

    if len(trimmedValue) > maxLength:
        raise ValueError(f"input exceeds max length of {maxLength}")

    disallowedChars = ["<", ">", ";"]
    for ch in disallowedChars:
        if ch in trimmedValue:
            raise ValueError(f"input contains disallowed character: {ch}")

    return trimmedValue
