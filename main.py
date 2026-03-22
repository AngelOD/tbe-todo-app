import uuid
import re

import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText

from models import Task
from models.enums import TaskState
from db import init_db, add_task, get_all_tasks, remove_task, update_task
from add_task_dialog import AddTaskDialog

# Optional dependencies
try:
    from tkhtmlview import HTMLLabel
    import markdown2
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


class TbeToDo:
    def __init__(self):
        self.tasks = {}
        self.selected_task: Task | None = None

        self.app: tb.Window | None = None
        self.task_dependent_buttons: list[tb.Button] = []
        self.task_info: ScrolledText | None = None
        self.task_list: tb.Treeview | None = None

        init_db()

        self.setup_ui()
        self.populate_task_list()

        self.app.mainloop()

    def setup_ui(self):
        self.app = tb.Window(title="TBE ToDo", themename="superhero")
        self.app.geometry("1200x800")

        self.setup_top_bar()
        self.setup_main_content()

    def setup_info_frame(self, main_content: tb.Frame):
        """Info frame on the right side"""
        info_frame = tb.Frame(main_content, bootstyle=PRIMARY, width=300)
        info_frame.pack(side=RIGHT, fill=Y)
        info_frame.pack_propagate(False)

        # TODO: Implement markdown rendering for task descriptions
        # if HAS_MARKDOWN:
            # html_version = markdown2.markdown(task.note)
            # self.task_info = HTMLLabel(info_frame, html=html_version, padding=20)
            # self.task_info.pack(fill=BOTH, expand=True)

        self.task_info = ScrolledText(info_frame, bootstyle=LIGHT, padding=10, autohide=True, wrap=WORD, font=("Helvetica", 10))
        self.task_info.pack(fill=BOTH, expand=True)

        # Set up styles
        self.task_info.tag_config("title", font=("Arial", 18, "bold underline"))
        self.task_info.tag_config("h2", font=("Arial", 14, "bold"))
        self.task_info.tag_config("bold", font=("Helvetica", 10, "bold"))
        self.task_info.tag_config("italic", font=("Helvetica", 10, "italic"))
        self.task_info.tag_config("bold_italic", font=("Helvetica", 10, "bold italic"))

        self.task_info.text.configure(state="disabled")

    def setup_main_content(self):
        """Main section with task list and info frame"""
        main_content = tb.Frame(self.app, bootstyle=LIGHT)
        main_content.pack(fill=BOTH, expand=True)

        self.setup_info_frame(main_content)
        self.setup_task_list(main_content)

    def setup_task_list(self, main_content: tb.Frame):
        """Task list on the left side"""
        self.task_list = tb.Treeview(main_content, columns=("state", "importance"), selectmode=BROWSE,
                                     bootstyle=(LIGHT, SUNKEN))
        self.task_list.pack(fill=BOTH, expand=True)

        self.task_list.heading("#0", text="Task")
        self.task_list.heading("state", text="State")
        self.task_list.heading("importance", text="Importance")

        # bold, italic, underline, overstrike
        self.task_list.tag_configure("completed", background="green", foreground="white", font=("", 10, "overstrike"))

        self.task_list.bind("<<TreeviewSelect>>", self._on_task_selected)

    def setup_top_bar(self):
        """Set up top bar with buttons"""
        top_bar = tb.Frame(self.app, bootstyle=SECONDARY)
        top_bar.pack(fill=X, padx=5, pady=5)

        tb.Button(top_bar, text="Add Task", bootstyle=SUCCESS, command=self._on_add_task).pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons = [
            tb.Button(top_bar, text="Add Subtask", bootstyle=SUCCESS, command=self._on_add_subtask, state=DISABLED),
            tb.Button(top_bar, text="Edit Task", bootstyle=WARNING, command=self._on_edit_task, state=DISABLED),
            tb.Menubutton(top_bar, text="Set task state", bootstyle=INFO, state=DISABLED),
            tb.Button(top_bar, text="Remove Task", bootstyle=DANGER, command=self._on_remove_task, state=DISABLED),
        ]

        self.task_dependent_buttons[0].pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons[1].pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons[2].pack(side=LEFT, padx=5, pady=5)
        self.task_dependent_buttons[3].pack(side=RIGHT, padx=5, pady=5)

        menu_btn = self.task_dependent_buttons[2]

        menu = tb.Menu(menu_btn, tearoff=False)
        for state in TaskState:
            menu.add_command(label=state.value, command=self._get_state_selector_lambda(state))

        menu_btn["menu"] = menu

    def populate_task_list(self):
        cur_selected = None

        if self.selected_task is not None:
            cur_selected = self.selected_task.id

        db_tasks = get_all_tasks()
        self.tasks = {}

        if len(db_tasks) == 0:
            # No need to populate the list if there are no tasks
            return

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

        if cur_selected is not None:
            self.task_list.see(cur_selected)
            self.task_list.selection_set([cur_selected])
            self._on_task_selected(None)

    def _get_state_selector_lambda(self, state: TaskState):
        def _lambda():
            if self.selected_task is not None:
                self.selected_task.state = state
                update_task(self.selected_task)
                self.populate_task_list()

        return _lambda

    def _get_tags_for_task(self, task: Task) -> tuple[str]:
        tags = []

        if task.is_completed():
            tags.append("completed")

        return tuple(tags)

    def _insert_markdown(self, text: str):
        part_text: str | None
        part_tag: str | None

        parts = re.split(r"(\*\*.*?\*\*|__.*?__|\{h2}.*?\{/h2})", text)

        for i, part in enumerate(parts):
            part_text = None
            part_tag = None

            if part.startswith("**") and part.endswith("**"):
                if part.startswith("**__") and part.endswith("__**"):
                    part_text = part[4:-4]
                    part_tag = "bold_italic"
                else:
                    part_text = part[2:-2]
                    part_tag = "bold"
            elif part.startswith("__") and part.endswith("__"):
                if part.startswith("__**") and part.endswith("**__"):
                    part_text = part[4:-4]
                    part_tag = "bold_italic"
                else:
                    part_text = part[2:-2]
                    part_tag = "italic"
            elif part.startswith("{h2}") and part.endswith("{/h2}"):
                part_text = part[4:-5]
                part_tag = "h2"
            else:
                part_text = part

            if part_text is not None:
                if part_tag is not None:
                    self.task_info.insert(END, part_text, part_tag)
                else:
                    self.task_info.insert(END, part_text)

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

        self._update_task_info()

        for button in self.task_dependent_buttons:
            button.configure(state=NORMAL if self.selected_task is not None else DISABLED)

    def _update_task_info(self):
        self.task_info.text.configure(state="normal")
        self.task_info.delete("1.0", "end")

        if self.selected_task is not None:
            self.task_info.insert(END, "Task Notes", "title")
            self.task_info.insert(END, "\n\n")

            if self.selected_task.note is not None:
                self._insert_markdown(self.selected_task.note)

        self.task_info.text.configure(state="disabled")


if __name__ == "__main__":
    TbeToDo()