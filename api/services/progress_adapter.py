from poster_maker.utils.progress import ProgressCallback
from api.services.task_manager import TaskManager
from api.schemas import TaskStatus

class APIProgressCallback(ProgressCallback):
    """
    Progress callback that updates the TaskManager.
    """
    def __init__(self, task_id: str, task_manager: TaskManager):
        self.task_id = task_id
        self.task_manager = task_manager
        self.total = 0
        self.current = 0

    def on_start(self, total_items: int, description: str = "") -> None:
        self.total = total_items
        self.current = 0
        self.task_manager.update_task(
            self.task_id, 
            status=TaskStatus.PROCESSING,
            progress=0, 
            message=description
        )

    def on_update(self, increment: int = 1, message: str = "") -> None:
        self.current += increment
        percentage = int((self.current / self.total) * 100) if self.total > 0 else 0
        # Clamp to 100
        percentage = min(percentage, 100)
        
        self.task_manager.update_task(
            self.task_id, 
            progress=percentage, 
            message=message
        )

    def on_complete(self) -> None:
        self.task_manager.update_task(
            self.task_id, 
            progress=100, 
            message="Processing complete"
        )
