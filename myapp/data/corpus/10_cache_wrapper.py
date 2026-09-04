class SimpleCache:
    """A tiny in-memory cache wrapper around an arbitrary compute function.

    Not thread-safe; intended for single-process memoization where an
    unbounded dict would grow too large over a long-running process.
    """

    def __init__(self, maxEntries=100):
        self.maxEntries = maxEntries
        self.cacheStore = {}

    def getOrCompute(self, cacheKey, computeFn):
        if cacheKey in self.cacheStore:
            return self.cacheStore[cacheKey]

        computedValue = computeFn()
        if len(self.cacheStore) >= self.maxEntries:
            self.cacheStore.pop(next(iter(self.cacheStore)))

        self.cacheStore[cacheKey] = computedValue
        return computedValue
