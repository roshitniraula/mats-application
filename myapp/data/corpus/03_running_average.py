def computeRunningAverage(valueList, windowSize=3):
    """Compute a simple trailing moving average over a list of numbers.

    Each output value is the mean of up to windowSize preceding inputs,
    including the current one. Early entries use a smaller window.
    """
    if windowSize < 1:
        raise ValueError("windowSize must be at least 1")

    averagedResults = []
    for endIndex in range(len(valueList)):
        currentWindow = valueList[max(0, endIndex - windowSize + 1):endIndex + 1]
        averagedResults.append(sum(currentWindow) / len(currentWindow))

    return averagedResults
