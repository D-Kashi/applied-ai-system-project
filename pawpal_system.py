from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from datetime import datetime
import uuid

# /c:/Users/dusha/Pawpal/pawpal_system.py
"""
Implemented classes for pawpal system.
Owner -> Schedule -> Task; Tasks archived when completed unless explicitly deleted.
"""


@dataclass
class Pet:
    name: str
    type: str
    gender: str


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    time: datetime = field(default_factory=datetime.now)
    completed: bool = False
    pet: Optional[Pet] = None

    def mark_completed(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as incomplete."""
        self.completed = False


@dataclass
class Schedule:
    tasks: List[Task] = field(default_factory=list)
    tasks_by_id: Dict[str, Task] = field(default_factory=dict)
    archived_tasks: Dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a new active task to the schedule unless it already exists."""
        if task.id in self.tasks_by_id or task.id in self.archived_tasks:
            return
        self.tasks.append(task)
        self.tasks_by_id[task.id] = task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by id from active or archived collections."""
        return self.tasks_by_id.get(task_id) or self.archived_tasks.get(task_id)

    def set_task_completed(self, task_id: str) -> bool:
        """Mark an active task completed and move it to the archive."""
        task = self.tasks_by_id.get(task_id)
        if not task:
            return False
        task.mark_completed()
        # move to archive
        try:
            self.tasks.remove(task)
        except ValueError:
            pass
        del self.tasks_by_id[task_id]
        self.archived_tasks[task_id] = task
        return True

    def set_task_incomplete(self, task_id: str) -> bool:
        """Restore an archived task to active (mark incomplete)."""
        task = self.archived_tasks.get(task_id)
        if not task:
            return False
        task.mark_incomplete()
        del self.archived_tasks[task_id]
        self.tasks.append(task)
        self.tasks_by_id[task_id] = task
        return True

    def remove_completed(self) -> List[Task]:
        """Permanently remove and return all archived (completed) tasks."""
        removed = list(self.archived_tasks.values())
        self.archived_tasks.clear()
        return removed

    def delete_archived(self, task_id: str) -> bool:
        """Delete a specific archived task by id."""
        if task_id in self.archived_tasks:
            del self.archived_tasks[task_id]
            return True
        return False

    def get_pending_tasks(self) -> List[Task]:
        """Return a list of currently active (pending) tasks."""
        return list(self.tasks)

    def get_completed_tasks(self) -> List[Task]:
        """Return a list of archived (completed) tasks."""
        return list(self.archived_tasks.values())


@dataclass
class Owner:
    name: str
    schedule: Schedule = field(default_factory=Schedule)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's pet list."""
        self.pets.append(pet)

    def add_task(self, task: Task) -> None:
        """Add a task to the owner's schedule."""
        self.schedule.add_task(task)

    def view_tasks(self, completed: Optional[bool] = None) -> List[Task]:
        """View pending, completed, or all tasks depending on 'completed' arg."""
        if completed is None:
            return self.schedule.get_pending_tasks() + self.schedule.get_completed_tasks()
        return self.schedule.get_completed_tasks() if completed else self.schedule.get_pending_tasks()

    def change_task_status(self, task_id: str, completed: bool) -> bool:
        """Change a task's status between completed and incomplete."""
        if completed:
            return self.schedule.set_task_completed(task_id)
        return self.schedule.set_task_incomplete(task_id)
