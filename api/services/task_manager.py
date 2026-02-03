import uuid
from typing import Dict, Optional, Any
from api.schemas import TaskResponse, TaskStatus

class TaskManager:
    """
    Manages the state of background tasks in memory.
    """
    def __init__(self):
        self._tasks: Dict[str, TaskResponse] = {}

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskResponse(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            progress=0,
            message="Task queued"
        )
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Get the current state of a task."""
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, status: TaskStatus = None, 
                    progress: int = None, message: str = None, 
                    result: Dict[str, Any] = None, error: str = None) -> None:
        """Update the state of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return

        if status:
            task.status = status
        if progress is not None:
            task.progress = progress
        if message:
            task.message = message
        if result:
            task.result = result
        if error:
            task.error = error
            task.status = TaskStatus.FAILED
