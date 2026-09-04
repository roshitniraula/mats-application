def fetchUserData(userId):
    """Mocked fetch of a user record by id (no real network call).

    Stands in for a small API client method — in a real client this
    would issue an HTTP GET and parse the JSON body.
    """
    fakeDatabase = {
        1: {"name": "Alice", "role": "admin"},
        2: {"name": "Bob", "role": "member"},
    }

    userRecord = fakeDatabase.get(userId)
    if userRecord is None:
        raise KeyError(f"no user with id {userId}")

    return userRecord
