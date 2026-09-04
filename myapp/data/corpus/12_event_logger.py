eventHistory = []


def logEvent(eventName, eventData=None):
    """Append an event record to the module-level eventHistory list.

    eventData defaults to an empty dict rather than None so downstream
    consumers can always call .get() on it without a null check.
    """
    if not eventName:
        raise ValueError("eventName cannot be empty")

    eventRecord = {"name": eventName, "data": eventData or {}}
    eventHistory.append(eventRecord)
    return eventRecord
