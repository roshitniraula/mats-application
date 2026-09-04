class TaskQueue:
    """A minimal FIFO task queue with no priority ordering.

    Backed by a plain list; fine for small queues where O(n) dequeue
    performance from list.pop(0) isn't a concern.
    """

    def __init__(self):
        self.pendingTasks = []

    def enqueueTask(self, taskItem):
        self.pendingTasks.append(taskItem)

    def dequeueTask(self):
        if not self.pendingTasks:
            return None
        return self.pendingTasks.pop(0)
