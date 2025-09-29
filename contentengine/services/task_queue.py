"""Task queue service implementation."""

import asyncio
from typing import Set

from contentengine.core.interfaces import ITaskQueue
from contentengine.models.task import CrawlTask


class TaskQueueService(ITaskQueue):
    """Service for managing crawl task queue."""
    
    def __init__(self):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.seen_queue: Set[str] = set()
        self._counter = 0
        self.priority_num = {"high": 0, "medium": 1, "low": 2}
    
    async def add_task(self, task: CrawlTask):
        """Add task to queue with deduplication."""
        if task.url in self.seen_queue:
            return
        
        self.seen_queue.add(task.url)
        self._counter += 1
        
        priority_value = self.priority_num.get(task.priority, 2)
        await self.queue.put((priority_value, self._counter, task))
    
    async def get_task(self) -> CrawlTask:
        """Get next task from queue."""
        priority, counter, task = await self.queue.get()
        return task
    
    async def join(self):
        """Wait for all tasks to complete."""
        await self.queue.join()
    
    def task_done(self):
        """Mark task as done."""
        self.queue.task_done()
    
    def qsize(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()
    
    def clear_seen(self):
        """Clear seen URLs set."""
        self.seen_queue.clear()