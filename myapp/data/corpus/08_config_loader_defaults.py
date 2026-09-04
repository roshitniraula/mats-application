defaultSettings = {
    "timeout": 30,
    "retryCount": 3,
    "logLevel": "INFO",
}


def loadSettingsWithDefaults(userSettings):
    """Merge user-provided settings over the module-level defaultSettings.

    Any key present in userSettings overrides the corresponding default;
    keys not mentioned by the caller fall back to defaultSettings.
    """
    mergedSettings = dict(defaultSettings)
    mergedSettings.update(userSettings)
    return mergedSettings
