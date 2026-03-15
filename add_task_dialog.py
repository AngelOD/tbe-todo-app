import ttkbootstrap as tb
from ttkbootstrap.constants import *
from models.enums import TaskImportance, TaskState
from models import Task

class AddTaskDialog(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(title="Add Task", size=(400, 350), resizable=(False, False))
        self.position_center()

        self.grab_set()

        self.result = None

        # Setup container with padding
        container = tb.Frame(self, padding=20)
        container.pack(fill=BOTH, expand=YES)

        # ----- Title Entry -----
        tb.Label(container, text="Title:").pack(fill=X, pady=(0, 5))
        self.title_var = tb.StringVar()
        self.title_entry = tb.Entry(container, textvariable=self.title_var)
        self.title_entry.pack(fill=X, pady=(0, 15))
        self.title_entry.focus_set()

        # ----- Importance Dropdown -----
        tb.Label(container, text="Importance:").pack(fill=X, pady=(0, 5))
        self.importance_var = tb.StringVar(value=TaskImportance.MEDIUM.value)
        self.importance_combo = tb.Combobox(
            container,
            textvariable=self.importance_var,
            values=[e.value for e in TaskImportance],
            state=READONLY
        )
        self.importance_combo.pack(fill=X, pady=(0, 15))

        # Buttons
        btn_frame = tb.Frame(container)
        btn_frame.pack(fill=X)

        self.submit_btn = tb.Button(btn_frame, text="Create Task", bootstyle=SUCCESS, command=self.on_submit)
        self.submit_btn.pack(side=RIGHT, padx=5)

        self.cancel_btn = tb.Button(btn_frame, text="Cancel", bootstyle=DANGER, command=self.destroy)
        self.cancel_btn.pack(side=RIGHT)

    def on_submit(self):
        self.result = {
            "title": self.title_var.get(),
        }
        self.destroy()