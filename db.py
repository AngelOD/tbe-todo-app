import datetime
import sqlite3
from typing import List
from models import Task


db_name = "todo_list.db"

latest_tasks_table_version = 2


def adapt_datetime_iso(val):
    return val.replace(tzinfo=None).isoformat()

def convert_datetime(val):
    return datetime.datetime.fromisoformat(val.decode())

sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime)


def init_db() -> None:
    """Initialize the SQLite database for the application."""

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS table_versions (
                table_name TEXT PRIMARY KEY,
                version INTEGER NOT NULL
            )
        """)

        # Create or migrate tasks table
        tasks_table_version = _get_table_version("tasks")
        if tasks_table_version < 1:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    title TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    importance TEXT,
                    note TEXT,
                    external_id TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks (parent_id)")
            _set_table_version("tasks", latest_tasks_table_version)
        elif tasks_table_version < 2:
            cursor.execute("ALTER TABLE tasks ADD COLUMN external_id TEXT")
            _set_table_version("tasks", latest_tasks_table_version)

def add_task(task: Task) -> None:
    """Add a task to the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        query = "INSERT OR REPLACE INTO tasks (id, parent_id, title, level, state, importance, note, external_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        params = (task.id, task.parent_id, task.title, task.level, task.state, task.importance, task.note, task.external_id)
        cursor.execute(query, params)

def get_all_tasks() -> List[Task]:
    """Get all tasks from the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, parent_id, title, level, state, importance, note, external_id FROM tasks")

        db_tasks = cursor.fetchall()

        tasks = []
        for row in db_tasks:
            task = Task(id=row[0], parent_id=row[1], title=row[2], level=row[3], state=row[4], importance=row[5], note=row[6], external_id=row[7])
            tasks.append(task)

        return sorted(tasks)

def remove_task(task_id: str) -> None:
    """Remove a task from the database."""
    to_remove = _get_all_ids_for_removal(task_id)

    print(f"Removing task {task_id} (total deletions: {len(to_remove)})")

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        query = "DELETE FROM tasks WHERE id=?"
        params = [(id,) for id in to_remove]
        cursor.executemany(query, params)


def save_all_tasks(tasks: List[Task]) -> None:
    """Save all tasks to the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        query = "INSERT OR REPLACE INTO tasks (id, parent_id, title, level, state, importance, note, external_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        params = [(t.id, t.parent_id, t.title, t.level, t.state, t.importance, t.note, t.external_id) for t in tasks]
        cursor.executemany(query, params)

def update_task(task: Task) -> None:
    """Update a task in the database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        query = "UPDATE tasks SET parent_id=?, title=?, level=?, state=?, importance=?, note=?, external_id=? WHERE id=?"
        params = (task.parent_id, task.title, task.level, task.state, task.importance, task.note, task.external_id, task.id)
        cursor.execute(query, params)


# ---- Private Functions ----
def _get_all_ids_for_removal(task_id: str) -> List[str]:
    """Get all IDs for tasks to be removed."""
    to_remove = []
    to_check = [task_id]

    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        while True:
            if len(to_check) == 0:
                break

            next_task_id = to_check.pop()
            to_remove.append(next_task_id)

            cursor.execute("SELECT id FROM tasks WHERE parent_id=?", (next_task_id,))
            subtask_ids = [row[0] for row in cursor.fetchall()]
            to_check.extend(subtask_ids)

    return to_remove

def _get_table_version(table_name: str) -> int:
    """Get the version of a table in the SQLite database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT version FROM table_versions WHERE table_name=?", (table_name,))
        row = cursor.fetchone()

        return row[0] if row else 0

def _set_table_version(table_name: str, version: int) -> None:
    """Set the version of a table in the SQLite database."""
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO table_versions (table_name, version) VALUES (?, ?)", (table_name, version))
