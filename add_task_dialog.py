import ttkbootstrap as tb
from ttkbootstrap.constants import *
from models.enums import TaskImportance
from models import Task

class AddTaskDialog(tb.Toplevel):
    def __init__(self, parent: tb.Window | None, task: Task | None = None, is_root: bool = False):
        super().__init__(title="Add Task", size=(600, 700), resizable=(False, False))

        self.position_center()
        self.grab_set()

        self.result = None

        # Setup container with padding
        container = tb.Frame(self, padding=20)
        container.pack(fill=BOTH, expand=YES)

        # ----- Title Entry -----
        tb.Label(container, text="Title:").pack(fill=X, pady=(0, 5))
        self.title_var = tb.StringVar(value=task.title if task else None)
        self.title_entry = tb.Entry(container, textvariable=self.title_var)
        self.title_entry.pack(fill=X, pady=(0, 15))
        self.title_entry.focus_set()

        # ----- External ID -----
        tb.Label(container, text="External ID:").pack(fill=X, pady=(0, 5))
        self.external_id_var = tb.StringVar(value=task.external_id if task else None)
        self.external_id_entry = tb.Entry(container, textvariable=self.external_id_var)
        self.external_id_entry.pack(fill=X, pady=(0, 15))

        # ----- Importance Dropdown -----
        self.importance_var = tb.StringVar()
        if is_root:
            tb.Label(container, text="Importance:").pack(fill=X, pady=(0, 5))
            self.importance_var.set(TaskImportance(task.importance).value if task and task.importance else TaskImportance.MEDIUM.value)
            self.importance_combo = tb.Combobox(
                container,
                textvariable=self.importance_var,
                values=[e.value for e in TaskImportance],
                state=READONLY
            )
            self.importance_combo.pack(fill=X, pady=(0, 15))

        # ----- Notes -----
        tb.Label(container, text="Notes:").pack(fill=X, pady=(0, 5))
        self.notes_text = tb.Text(container, wrap=WORD)
        ys = tb.Scrollbar(container, orient=VERTICAL, command=self.notes_text.yview)
        self.notes_text.config(yscrollcommand=ys.set)
        self.notes_text.pack(fill=BOTH, expand=YES, pady=(0, 15))

        self.notes_text.delete("1.0", "end")
        if task is not None and task.note is not None:
            self.notes_text.insert("1.0", task.note)

        # Buttons
        btn_frame = tb.Frame(container)
        btn_frame.pack(fill=X)

        submit_button_text = "Create Task" if not task else "Update Task"
        if not is_root:
            submit_button_text = submit_button_text.replace("Task", "Subtask")

        self.submit_btn = tb.Button(btn_frame, text=submit_button_text, bootstyle=SUCCESS, command=self.on_submit)
        self.submit_btn.pack(side=RIGHT, padx=5)

        self.cancel_btn = tb.Button(btn_frame, text="Cancel", bootstyle=DANGER, command=self.destroy)
        self.cancel_btn.pack(side=RIGHT)

    def on_submit(self):
        self.result = {
            "title": self.title_var.get(),
            "external_id": self.external_id_var.get(),
            "importance": TaskImportance(self.importance_var.get()) if self.importance_var.get() else None,
            "notes": self.notes_text.get("1.0", "end")
        }
        self.destroy()