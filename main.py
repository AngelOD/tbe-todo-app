import random
import uuid
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from models import Task
from models.enums import TaskImportance, TaskState
from db import init_db, add_task, get_all_tasks, save_all_tasks
from add_task_dialog import AddTaskDialog


class TbeToDo:
    def __init__(self):
        self.tasks: list[Task] = []

        self.app: tb.Window | None = None
        self.task_list: tb.Treeview | None = None

        init_db()

        self.setup_ui()
        self.populate_task_list()

        self.app.mainloop()

    def setup_ui(self):
        self.app = tb.Window(title="TBE ToDo", themename="vapor")
        self.app.geometry("1200x800")

        top_bar = tb.Frame(self.app, bootstyle=SECONDARY)
        top_bar.pack(fill=X, padx=5, pady=5)

        tb.Button(top_bar, text="Add Task", bootstyle=SUCCESS, command=self._on_add_task).pack(side=LEFT, padx=5, pady=5)
        tb.Button(top_bar, text="Clear Tasks", bootstyle=DANGER, command=self.populate_task_list).pack(side=LEFT, padx=5, pady=5)

        main_grid = tb.Frame(self.app, bootstyle=LIGHT)
        main_grid.pack(fill=BOTH, expand=True)

        info_frame = tb.Frame(main_grid, bootstyle=PRIMARY, width=300)
        info_frame.pack(side=RIGHT, fill=Y)
        info_frame.pack_propagate(False)

        task_info = tb.Frame(info_frame, bootstyle=LIGHT)
        task_info.pack(side=TOP, padx=5, pady=5, fill=X)

        tb.Label(task_info, text="Task Info").pack(fill=X, expand=True, padx=5, pady=5)

        self.task_list = tb.Treeview(main_grid, columns=("State", "Importance"), selectmode=BROWSE, bootstyle=(LIGHT, SUNKEN))
        self.task_list.pack(fill=BOTH, expand=True)
        self.task_list.bind("<<TreeviewSelect>>", lambda e: print(self.task_list.focus()))

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

        tasks = get_all_tasks()

        for i in self.task_list.get_children():
            self.task_list.delete(i)

        for t in tasks:
            if not self.task_list.exists(t.id):
                self.task_list.insert(
                    t.parent_id if t.parent_id is not None else "",
                    "end",
                    id=t.id,
                    text=t.title,
                    values=(t.state, t.importance),
                    open=True if t.level == 0 else False,
                )

    def _on_add_task(self):
        dialog = AddTaskDialog(self.app)
        self.app.wait_window(dialog)

        print(dialog.result)


if __name__ == "__main__":
    TbeToDo()
