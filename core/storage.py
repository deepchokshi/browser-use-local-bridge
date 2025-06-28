from collections import defaultdict
from typing import Dict, List, Optional

from models.task import Task, TaskStatus

class TaskStorage:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Task]] = defaultdict(dict)

    def add_task(self, user_id: str, task: Task):
        self._tasks[user_id][task.id] = task

    def get_task(self, user_id: str, task_id: str) -> Optional[Task]:
        return self._tasks.get(user_id, {}).get(task_id)

    def list_tasks(self, user_id: str, page: int, page_size: int) -> List[Task]:
        user_tasks = list(self._tasks.get(user_id, {}).values())
        start = (page - 1) * page_size
        end = start + page_size
        return user_tasks[start:end]

    def update_task_status(self, user_id: str, task_id: str, status: TaskStatus):
        task = self.get_task(user_id, task_id)
        if task:
            task.status = status

task_storage = TaskStorage()