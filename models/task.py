import uuid
from dataclasses import dataclass, field

from models.enums import TaskImportance, TaskState

@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str | None = None
    title: str = ""
    level: int = 0
    importance: TaskImportance | None = None
    state: TaskState = TaskState.NEW
    note: str | None = None

    def is_completed(self) -> bool:
        return self.state == TaskState.COMPLETED

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False

        return self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, Task):
            return False

        if self.level != other.level:
            return self.level < other.level

        if self.is_completed() != other.is_completed():
            return other.is_completed()

        if self.importance != other.importance and self.importance is not None and other.importance is not None:
            importance_order = list(TaskImportance)
            return importance_order.index(self.importance) < importance_order.index(other.importance)

        return self.title < other.title
