def tokenizeLine(rawLine, delimiter=","):
    """Split a raw text line into a list of cleaned, non-empty tokens.

    Leading/trailing whitespace is stripped from each piece, and any
    resulting empty strings are dropped from the output.
    """
    splitParts = rawLine.split(delimiter)

    cleanTokens = []
    for part in splitParts:
        strippedPart = part.strip()
        if strippedPart:
            cleanTokens.append(strippedPart)

    return cleanTokens
