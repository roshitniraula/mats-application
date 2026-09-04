import json


def loadConfigFile(filePath):
    """Read a JSON config file from disk and return the parsed dict.

    Raises the underlying exception unchanged if the file is missing
    or contains invalid JSON — callers are expected to handle that.
    """
    with open(filePath, "r") as configFile:
        fileContents = configFile.read()

    if not fileContents.strip():
        raise ValueError(f"config file is empty: {filePath}")

    return json.loads(fileContents)
