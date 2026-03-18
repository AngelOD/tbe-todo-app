import random
import uuid
import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from models import Task
from models.enums import TaskImportance, TaskState
from db import init_db, add_task, get_all_tasks, remove_task, save_all_tasks, update_task
from add_task_dialog import AddTaskDialog


class TbeToDo:
    def __init__(self):
        self.tasks = {}
        self.selected_task: Task | None = None

        self.app: tb.Window | None = None
        self.task_dependent_buttons: list[tb.Button] = []
        self.task_list: tb.Treeview | None = None

        init_db()

        self.setup_ui()
        self.populate_task_list()

        self.app.mainloop()

    def setup_ui(self):
        self.app = tb.Window(title="TBE ToDo", themename="superhero")
        self.app.geometry("1200x800")

        # Set up top bar with buttons
        top_bar = tb.Frame(self.app, bootstyle=SECONDARY)
        top_bar.pack(fill=X, padx=5, pady=5)

        tb.Button(top_bar, text="Add Task", bootstyle=SUCCESS, command=self._on_add_task).pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons = [
            tb.Button(top_bar, text="Add Subtask", bootstyle=SUCCESS, command=self._on_add_subtask, state=DISABLED),
            tb.Button(top_bar, text="Edit Task", bootstyle=WARNING, command=self._on_edit_task, state=DISABLED),
            tb.Button(top_bar, text="Remove Task", bootstyle=DANGER, command=self._on_remove_task, state=DISABLED),
        ]

        self.task_dependent_buttons[0].pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons[1].pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons[2].pack(side=RIGHT, padx=5, pady=5)

        # Main section with task list and info frame
        main_grid = tb.Frame(self.app, bootstyle=LIGHT)
        main_grid.pack(fill=BOTH, expand=True)

        # Info frame on the right side
        info_frame = tb.Frame(main_grid, bootstyle=PRIMARY, width=300)
        info_frame.pack(side=RIGHT, fill=Y)
        info_frame.pack_propagate(False)

        task_info = tb.Frame(info_frame, bootstyle=LIGHT)
        task_info.pack(side=TOP, padx=5, pady=5, fill=X)

        tb.Label(task_info, text="Task Info").pack(fill=X, expand=True, padx=5, pady=5)

        # Task list on the left side
        self.task_list = tb.Treeview(main_grid, columns=("state", "importance"), selectmode=BROWSE, bootstyle=(LIGHT, SUNKEN))
        self.task_list.pack(fill=BOTH, expand=True)

        self.task_list.heading("#0", text="Task")
        self.task_list.heading("state", text="State")
        self.task_list.heading("importance", text="Importance")

        # bold, italic, underline, overstrike
        self.task_list.tag_configure("completed", background="green", foreground="white", font=("", 10, "overstrike"))

        self.task_list.bind("<<TreeviewSelect>>", self._on_task_selected)

    def populate_task_list(self):
        if len(get_all_tasks()) == 0:
            tasks = []

            for i in range(20):
                base_parent = Task(id=str(uuid.uuid4()), title=f"Task {i}", level=0, importance=random.choice(list(TaskImportance)), state=random.choice(list(TaskState)))
                tasks.append(base_parent)

                for j in range(3):
                    sub_parent = Task(id=str(uuid.uuid4()), title=f"Subtask {i}.{j}", level=1, parent_id=base_parent.id, state=random.choice(list(TaskState)))
                    tasks.append(sub_parent)

                    for k in range(8):
                        child = Task(id=str(uuid.uuid4()), title=f"Subtask {i}.{j}.{k}", level=2, parent_id=sub_parent.id, state=random.choice(list(TaskState)))
                        tasks.append(child)

            save_all_tasks(tasks)

        db_tasks = get_all_tasks()
        self.tasks = {}

        for t in db_tasks:
            self.tasks[t.id] = t

        for i in self.task_list.get_children():
            self.task_list.delete(i)

        for t in self.tasks.values():
            if not self.task_list.exists(t.id):
                self.task_list.insert(
                    t.parent_id if t.parent_id is not None else "",
                    "end",
                    id=t.id,
                    text=t.title,
                    values=(t.state, t.importance if t.importance is not None else ""),
                    open=False,
                    tags=self._get_tags_for_task(t),
                )
            else:
                self.task_list.item(
                    t.id,
                    values=(t.state, t.importance if t.importance is not None else ""),
                    tags=self._get_tags_for_task(t),
                )

    def _get_tags_for_task(self, task: Task) -> tuple[str]:
        tags = []

        if task.is_completed():
            tags.append("completed")

        return tuple(tags)

    def _on_add_task(self):
        dialog = AddTaskDialog(self.app, is_root=True)
        self.app.wait_window(dialog)

        if dialog.result is not None:
            title = dialog.result["title"]
            importance = dialog.result["importance"] if "importance" in dialog.result else None
            state = TaskState.NEW

            add_task(Task(id=str(uuid.uuid4()), title=title, importance=importance, state=state, note=dialog.result["notes"]))

            self.populate_task_list()

    def _on_add_subtask(self):
        if self.selected_task is None:
            return

        dialog = AddTaskDialog(self.app, is_root=False)
        self.app.wait_window(dialog)

        if dialog.result is not None:
            parent_id = self.selected_task.id
            title = dialog.result["title"]
            importance = dialog.result["importance"] if "importance" in dialog.result else None
            state = TaskState.NEW

            add_task(Task(id=str(uuid.uuid4()), parent_id=parent_id, title=title, importance=importance, state=state, note=dialog.result["notes"]))

            self.populate_task_list()

    def _on_edit_task(self):
        if self.selected_task is None:
            return

        dialog = AddTaskDialog(self.app, self.selected_task, is_root=self.selected_task.level == 0)
        self.app.wait_window(dialog)

        if dialog.result is not None:
            self.selected_task.title = dialog.result["title"]
            self.selected_task.importance = dialog.result["importance"] if "importance" in dialog.result else None
            self.selected_task.note = dialog.result["notes"]

            update_task(self.selected_task)

            self.populate_task_list()

    def _on_remove_task(self):
        if self.selected_task is None:
            return

        res = Messagebox.yesno(f"Are you sure you want to remove {self.selected_task.title} (with subtasks)?\nThis CANNOT be undone!", "Really delete?", alert=True)

        if res != "Yes":
            return

        remove_task(self.selected_task.id)

        self.populate_task_list()

    def _on_task_selected(self, event):
        self.selected_task = self.tasks[self.task_list.focus()] if self.task_list.focus() else None
        print(self.selected_task)

        for button in self.task_dependent_buttons:
            button.configure(state=NORMAL if self.selected_task is not None else DISABLED)


if __name__ == "__main__":
    TbeToDo()
