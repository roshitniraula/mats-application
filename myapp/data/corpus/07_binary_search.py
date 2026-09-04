def binarySearch(sortedList, targetValue):
    """Return the index of targetValue in sortedList, or -1 if absent.

    Standard iterative binary search; assumes sortedList is sorted in
    ascending order and contains no duplicate handling beyond the first
    match found.
    """
    lowIndex = 0
    highIndex = len(sortedList) - 1

    while lowIndex <= highIndex:
        midIndex = (lowIndex + highIndex) // 2

        if sortedList[midIndex] == targetValue:
            return midIndex
        elif sortedList[midIndex] < targetValue:
            lowIndex = midIndex + 1
        else:
            highIndex = midIndex - 1

    return -1
