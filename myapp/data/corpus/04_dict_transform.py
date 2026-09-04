def mergeUserRecords(primaryRecord, secondaryRecord):
    """Merge two user-record dicts.

    Keys from secondaryRecord are used as a base, then overwritten by
    any matching keys present in primaryRecord (primary wins on conflict).
    """
    mergedResult = dict(secondaryRecord)
    mergedResult.update(primaryRecord)

    # Normalize the display name if both records happened to set it
    # differently, preferring whichever is longer as more descriptive.
    if "name" in primaryRecord and "name" in secondaryRecord:
        if len(secondaryRecord["name"]) > len(primaryRecord["name"]):
            mergedResult["name"] = secondaryRecord["name"]

    return mergedResult
