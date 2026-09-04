from datetime import datetime


def formatTimestamp(rawTimestamp, outputFormat="%Y-%m-%d %H:%M"):
    """Convert a unix timestamp into a human-readable string.

    outputFormat follows Python's strftime directives; the default
    produces a minute-resolution timestamp suitable for log lines.
    Raises ValueError if rawTimestamp is negative, since this codebase
    never deals with pre-1970 dates.
    """
    if rawTimestamp < 0:
        raise ValueError("rawTimestamp cannot be negative")

    parsedDatetime = datetime.fromtimestamp(rawTimestamp)
    return parsedDatetime.strftime(outputFormat)
