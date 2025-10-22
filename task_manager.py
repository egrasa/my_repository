""" A simple GUI application for managing tasks using Tkinter. """

import tkinter as tk
from tkinter import ttk, messagebox
from tasks_db import TasksDB

class TaskManagerApp:
    """ class for the Task Manager GUI application. """
    def __init__(self, master: tk.Tk):
        self.root = master
        self.root.title('Task Organizer')
        self.root.geometry('800x1000')
        self.db = TasksDB()
        self.current_category_filter = 'All'

        self._build_ui()
        self._load_tasks()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Form
        form = ttk.Frame(frame)
        form.pack(fill=tk.X)

        ttk.Label(form, text='Title:').grid(row=0, column=0, sticky=tk.W)
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var, width=40).grid(row=0, column=1, columnspan=3, sticky=tk.W)

        ttk.Label(form, text='Category:').grid(row=1, column=0, sticky=tk.W)
        self.category_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.category_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(form, text='Price:').grid(row=1, column=2, sticky=tk.W)
        self.price_var = tk.DoubleVar(value=0.0)
        ttk.Entry(form, textvariable=self.price_var, width=10).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(form, text='Level:').grid(row=2, column=0, sticky=tk.W)
        self.level_var = tk.IntVar(value=0)
        ttk.Spinbox(form, from_=0, to=10, textvariable=self.level_var, width=5).grid(row=2, column=1, sticky=tk.W)

        # 'Count' numeric counter (times completed) with increment/decrement
        self.done_var = tk.IntVar(value=0)
        ttk.Label(form, text='Count:').grid(row=2, column=2, sticky=tk.W)
        count_spin = ttk.Spinbox(form, from_=0, to=9999, textvariable=self.done_var, width=5)
        count_spin.grid(row=2, column=3, sticky=tk.W)
        # small inc/dec buttons
        ttk.Button(form, text='+', width=2, command=self._inc_count).grid(row=2, column=4, sticky=tk.W, padx=(4,0))
        ttk.Button(form, text='-', width=2, command=self._dec_count).grid(row=2, column=5, sticky=tk.W, padx=(4,0))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text='Add Task', command=self._add_task).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text='Edit Task', command=self._edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='Delete Task', command=self._delete_task).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text='Clear Form', command=self._clear_form).pack(side=tk.RIGHT)

        # Category filter
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text='Filter by category:').pack(side=tk.LEFT)
        self.filter_var = tk.StringVar(value='All')
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, state='readonly', width=30)
        self.filter_combo.pack(side=tk.LEFT, padx=6)
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self._on_category_filter_change())

        # Task list (added computed 'total' column: price * count)
        self.tree = ttk.Treeview(frame, columns=('title', 'category', 'price', 'total', 'level', 'done'), show='headings')
        # keep track of sort state: (column -> True for ascending, False for descending)
        self._sort_state = {}
        for col, heading in [('title','Title'),('category','Category'),('price','Price'),('total','Total'),('level','Level'),('done','Count')]:
            # attach a command to the heading to sort by that column
            self.tree.heading(col, text=heading, command=lambda c=col: self._on_heading_click(c))
            # make title column twice as wide by default; tune widths for numeric columns
            if col == 'title':
                default_width = 200
            elif col in ('price', 'level'):
                default_width = 80
            elif col == 'total':
                default_width = 100
            else:
                default_width = 100
            self.tree.column(col, width=default_width)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

    def _load_tasks(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        tasks = self.db.list_tasks()
        # ensure filter combobox is populated with available categories
        try:
            self._populate_category_filter(tasks)
        except (ValueError, TypeError):
            # don't let filter population break loading
            pass
        for t in tasks:
            if self.current_category_filter and self.current_category_filter != 'All':
                # treat empty/None categories as empty string
                cat = t['category'] or ''
                if cat != self.current_category_filter:
                    continue
            total = (t['price'] or 0.0) * (int(t['done']) if t['done'] is not None else 0)
            self.tree.insert('', tk.END, iid=t['id'], values=(t['title'], t['category'],
                                                              f"{t['price']:.2f}", f"{total:.2f}", t['level'],
                                                              str(t['done'])))

    def _add_task(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning('Validation', 'Title is required')
            return
        category = self.category_var.get().strip()
        price = self.price_var.get()
        level = self.level_var.get()
        done = int(self.done_var.get())
        # store count as integer in DB
        self.db.add_task(title, category, price, level, done)
        self._clear_form()
        # refresh category filter and tasks
        self._populate_category_filter()
        self._load_tasks()

    def _on_tree_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        tid = int(sel[0])
        item = self.tree.item(tid)
        vals = item['values']
        self.title_var.set(vals[0])
        self.category_var.set(vals[1])
        try:
            self.price_var.set(float(vals[2]))
        except ValueError:
            self.price_var.set(0.0)
        try:
            self.level_var.set(int(vals[3]))
        except (ValueError, TypeError):
            self.level_var.set(0)
        # done/count column stored as string in tree; convert to int safely
        try:
            self.done_var.set(int(vals[4]))
        except (ValueError, TypeError):
            self.done_var.set(0)

    def _on_heading_click(self, column: str):
        # toggle sort direction
        asc = self._sort_state.get(column, True)
        # perform sort
        self._sort_by(column, asc)
        # toggle for next time
        self._sort_state[column] = not asc

    def _sort_by(self, column: str, ascending: bool = True):
        # fetch all items
        items = [(self.tree.set(k, column), k) for k in self.tree.get_children('')]

        # attempt numeric conversion for numeric-like columns
        def try_num(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return val.lower() if isinstance(val, str) else val

        items = [(try_num(v), k) for (v, k) in items]
        items.sort(reverse=not ascending, key=lambda t: t[0])

        # reorder
        for index, (_val, k) in enumerate(items):
            self.tree.move(k, '', index)

        # update headings to show arrow
        for col in ('title', 'category', 'price', 'total', 'level', 'done'):
            base = col.capitalize() if col != 'done' else 'Done'
            arrow = ''
            if col == column:
                arrow = ' ▲' if ascending else ' ▼'
            self.tree.heading(col, text=base + arrow,
                              command=lambda c=col: self._on_heading_click(c))

    def _populate_category_filter(self, tasks=None):
        # populate the category combobox with distinct categories from tasks
        if tasks is None:
            tasks = self.db.list_tasks()
        cats = set()
        for t in tasks:
            if t['category']:
                cats.add(t['category'])
        choices = ['All'] + sorted(cats)
        # update combobox values without resetting the current selection if possible
        cur = self.filter_var.get() if hasattr(self, 'filter_var') else 'All'
        self.filter_combo['values'] = choices
        if cur in choices:
            self.filter_var.set(cur)
        else:
            self.filter_var.set('All')
            self.current_category_filter = 'All'

    def _on_category_filter_change(self):
        sel = self.filter_var.get()
        self.current_category_filter = sel
        self._load_tasks()

    def _inc_count(self):
        # increment the spinbox value and persist if a task is selected
        val = int(self.done_var.get())
        val += 1
        self.done_var.set(val)
        sel = self.tree.selection()
        if sel:
            tid = int(sel[0])
            # update DB and refresh
            self.db.update_task(tid, done=val)
            self._load_tasks()

    def _dec_count(self):
        val = int(self.done_var.get())
        if val <= 0:
            return
        val -= 1
        self.done_var.set(val)
        sel = self.tree.selection()
        if sel:
            tid = int(sel[0])
            self.db.update_task(tid, done=val)
            self._load_tasks()

    def _edit_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Edit', 'Select a task to edit')
            return
        tid = int(sel[0])
        self.db.update_task(tid, title=self.title_var.get().strip(),
                            category=self.category_var.get().strip(),
                            price=self.price_var.get(), level=self.level_var.get(),
                            done=int(self.done_var.get()))
        self._populate_category_filter()
        self._load_tasks()

    def _delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo('Delete', 'Select a task to delete')
            return
        tid = int(sel[0])
        if messagebox.askyesno('Delete', 'Delete selected task?'):
            self.db.delete_task(tid)
            self._populate_category_filter()
            self._load_tasks()

    def _clear_form(self):
        self.title_var.set('')
        self.category_var.set('')
        self.price_var.set(0.0)
        self.level_var.set(0)
        self.done_var.set(0)

if __name__ == '__main__':
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()
