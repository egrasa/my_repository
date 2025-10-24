"""A simple GUI application for managing tasks using Tkinter."""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from tkinter import filedialog as fd
import csv
from typing import Optional
import matplotlib.pyplot as plt
import ttkbootstrap as tb
from tasks_db import TasksDB


class TaskManagerApp:
    """ Main application class for Task Manager. """
    def __init__(self, master: Optional[tk.Tk] = None):
        # prefer master if provided, otherwise use ttkbootstrap darkly (assumed installed)
        if master is not None:
            self.root = master
            self._theme_engine = None
        else:
            # Create one ttkbootstrap Window and then probe/set its Style.
            # This avoids creating multiple top-level windows which caused
            # the empty window artifact during shutdown.
            preferred = ['slate', 'flatly', 'litera']
            chosen = None
            try:
                # create a single tb.Window (may raise if ttkbootstrap not usable)
                self.root = tb.Window(title="Task Organizer")
                try:
                    style_probe = tb.Style()
                    available = list(style_probe.theme_names())
                    for theme_name in preferred:
                        if theme_name in available:
                            chosen = theme_name
                            try:
                                style_probe.theme_use(chosen)
                            except (AttributeError, TypeError, tk.TclError):
                                # if we cannot switch, just continue
                                chosen = None
                            break
                except (AttributeError, TypeError, tk.TclError):
                    # unable to probe or set themes; continue with default
                    chosen = None
                if chosen:
                    self._theme_engine = f'ttkbootstrap ({chosen})'
                else:
                    self._theme_engine = 'ttkbootstrap (default)'
            except (AttributeError, TypeError, tk.TclError):
                # ttkbootstrap failed entirely; use plain Tk
                self.root = tk.Tk()
                self._theme_engine = None

        self.root.title("Task Organizer")
        self.root.geometry("900x800")

        # DB
        self.db = TasksDB()

        # state
        self.title_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.price_var = tk.DoubleVar(value=0.0)
        self.level_var = tk.IntVar(value=0)
        self.done_var = tk.IntVar(value=0)
        self.filter_var = tk.StringVar(value="All")
        self.current_category_filter = "All"
        # stringvar to show sum of visible totals
        self.total_sum_var = tk.StringVar(value="Total: $0.00")

        # column sort state: True means ascending next time
        self._sort_state = {}
        # category -> tag mapping and palette
        self._category_tag_map = {}
        # pleasant pastel palette for categories
        self._palette = [
            "#F88585",
            '#F9E2C2',
            '#F9F0C2',
            "#CFFD9B",
            "#AEFCDA",
            "#A5E2FA",
            "#FCDE8C",
            "#C1F3FF",
            "#B9C2FD",
            '#E8C2F9',
            "#DF97FC"
        ]

        self._build_ui()
        self._load_tasks()
        # small status label about theme engine (update window title)
        try:
            self.root.after(100,
                            lambda: self.root.title("Task Organizer - "
                                                    f"{self._theme_engine or 'default'}"))
        except (AttributeError, tk.TclError):
            pass

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Form
        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(form, textvariable=self.title_var, width=40).grid(row=0,
                                                                    column=1,
                                                                    columnspan=3,
                                                                    sticky=tk.W)

        ttk.Label(form, text="Category:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(form, textvariable=self.category_var, width=24).grid(row=1,
                                                                       column=1,
                                                                       sticky=tk.W)

        ttk.Label(form, text="Price:").grid(row=1, column=2, sticky=tk.W)
        ttk.Entry(form, textvariable=self.price_var, width=12).grid(row=1, column=3, sticky=tk.W)

        ttk.Label(form, text="Level:").grid(row=2, column=0, sticky=tk.W)
        ttk.Spinbox(form, from_=0, to=10, textvariable=self.level_var, width=6).grid(row=2,
                                                                                     column=1,
                                                                                     sticky=tk.W)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_frame, text="Add Task", command=self._add_task).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Edit Task", command=self._edit_task).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Delete Task", command=self._delete_task).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Reset Counts", command=self._reset_all_counts).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Export CSV", command=self._export_csv).pack(side=tk.LEFT,
                                                                                padx=6)
        # chart button to visualize Price vs Count
        ttk.Button(btn_frame, text="Grafica", command=self._show_chart).pack(side=tk.LEFT,
                                                                                padx=6)
        ttk.Button(btn_frame, text="Clear Form", command=self._clear_form).pack(side=tk.RIGHT)

        # Category filter
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text="Filter by category:").pack(side=tk.LEFT)
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                         state="readonly", width=30)
        self.filter_combo.pack(side=tk.LEFT, padx=6)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._on_category_filter_change())

        big_btn_font = tkfont.Font(size=12, weight="bold")
        plus_btn = tk.Button(filter_frame, text="+", width=3, font=big_btn_font,
                             command=self._inc_count)
        plus_btn.pack(side='right', padx=(8, 0))
        minus_btn = tk.Button(filter_frame, text="-", width=3, font=big_btn_font,
                              command=self._dec_count)
        minus_btn.pack(side='right', padx=(8, 0))

        # sum of totals label (placed under the filter controls)
        sum_frame = ttk.Frame(frame)
        sum_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(sum_frame, text="Sum of visible Totals:").pack(side=tk.LEFT)
        ttk.Label(sum_frame, textvariable=self.total_sum_var).pack(side=tk.LEFT, padx=(6, 0))

        # Task list with computed Total column
        cols = ("title", "category", "price", "total", "level", "done")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings")

        headings = [("title", "Title"), ("category", "Category"), ("price", "Price"),
                    ("total", "Total"), ("level", "Level"), ("done", "Count")]
        for col, heading in headings:
            # capture col in default arg
            self.tree.heading(col, text=heading, command=lambda c=col: self._on_heading_click(c))

        # set sensible column widths
        self.tree.column("title", width=260)
        self.tree.column("category", width=140)
        self.tree.column("price", width=80, anchor=tk.E)
        self.tree.column("total", width=100, anchor=tk.E)
        self.tree.column("level", width=80, anchor=tk.CENTER)
        self.tree.column("done", width=80, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _load_tasks(self):
        # load tasks from DB and populate treeview, applying category filter
        for row in self.tree.get_children():
            self.tree.delete(row)

        tasks = self.db.list_tasks()
        # populate category filter choices
        self._populate_category_filter(tasks)

        sum_total = 0.0
        for t in tasks:
            if self.current_category_filter and self.current_category_filter != "All":
                if t.get("category") != self.current_category_filter:
                    continue

            tid = str(t["id"]) if "id" in t else str(t.get("rowid", ""))
            price = float(t.get("price", 0.0) or 0.0)
            count = int(t.get("done", 0) or 0)
            total = price * count
            sum_total += total
            values = (t.get("title", ""), t.get("category", ""), f"{price:.2f}", f"{total:.2f}",
                      str(t.get("level", "")), str(count))
            # ensure there's a tag for this category and use it for row coloring
            cat = t.get("category") or ""
            tag = self._ensure_tag_for_category(cat)
            self.tree.insert("", tk.END, iid=tid, values=values, tags=(tag,))
        # update total sum label for currently visible rows
        try:
            self.total_sum_var.set(f"${sum_total:,.2f}")
        except (ValueError, TypeError):
            self.total_sum_var.set("$0.00")

    def _reset_all_counts(self):
        """Ask for confirmation and reset all tasks' done counters to zero."""
        if not messagebox.askyesno("Reset all counts",
                                   "Set all task counters to 0? This action cannot be undone."):
            return
        # fetch all tasks and set done=0
        tasks = self.db.list_tasks()
        updated = 0
        for t in tasks:
            tid = int(t.get("id") or t.get("rowid"))
            try:
                self.db.update_task(tid, done=0)
                updated += 1
            except (ValueError, TypeError):
                # ignore individual update failures but continue
                continue
        self._populate_category_filter()
        self._load_tasks()
        messagebox.askokcancel("Reset complete", f"Reset counters to 0 for {updated} tasks")

    def _export_csv(self):
        """Export currently visible rows to CSV. Ask whether full or partial export.

        Partial = only Title and Price. Full = all visible columns.
        """
        # ask the user for full or partial
        res = messagebox.askquestion("Export CSV",
                                     "Export full CSV? (No = partial Title+Price)",
                                     icon='question')
        partial = res == 'no'

        # choose save path
        out_path = fd.asksaveasfilename(title="Save CSV as", defaultextension=".csv",
                                        filetypes=[("CSV files", "*.csv")])
        if not out_path:
            return

        # build rows from currently visible items
        headers_full = ["Title", "Category", "Price", "Total", "Level", "Count"]
        headers_partial = ["Title", "Price"]

        try:
            with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers_partial if partial else headers_full)
                for iid in self.tree.get_children(''):
                    vals = self.tree.item(iid, 'values')
                    # vals order: title, category, price, total, level, done
                    if partial:
                        writer.writerow([vals[0], vals[2]])
                    else:
                        writer.writerow(list(vals))
        except (OSError, IOError) as e:
            messagebox.showerror("Export error", f"Failed to write CSV: {e}")
            return

        messagebox.askokcancel("Export complete", f"CSV saved to: {out_path}")

    def _ensure_tag_for_category(self, category: str) -> str:
        """Return a tag name for a category, creating and configuring it if needed.

        The color is chosen deterministically from a small palette.
        """
        # normalize empty
        cat_key = category or "__none__"
        if cat_key in self._category_tag_map:
            return self._category_tag_map[cat_key]

        # deterministic pick based on hash
        color = self._palette[abs(hash(cat_key)) % len(self._palette)]
        # small stable tag name
        tag_name = f"cat_{abs(hash(cat_key)) % 100000}"
        try:
            # configure tag background
            self.tree.tag_configure(tag_name, background=color)
        except tk.TclError:
            # if the underlying theme/widget doesn't support it, ignore
            pass
        self._category_tag_map[cat_key] = tag_name
        return tag_name

    def _populate_category_filter(self, tasks=None):
        if tasks is None:
            tasks = self.db.list_tasks()
        cats = set()
        for t in tasks:
            c = t.get("category")
            if c:
                cats.add(c)
        choices = ["All"] + sorted(cats)
        self.filter_combo["values"] = choices
        cur = self.filter_var.get() or "All"
        if cur in choices:
            self.filter_var.set(cur)
        else:
            self.filter_var.set("All")
            self.current_category_filter = "All"

    def _on_category_filter_change(self):
        self.current_category_filter = self.filter_var.get()
        self._load_tasks()

    def _on_tree_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        vals = self.tree.item(iid, "values")
        # values: title, category, price, total, level, done
        try:
            self.title_var.set(vals[0])
            self.category_var.set(vals[1])
            self.price_var.set(float(vals[2]))
            self.level_var.set(int(vals[4]))
            self.done_var.set(int(vals[5]))
        except (ValueError, TypeError, IndexError):
            # if something unexpected, fallback to safe defaults
            self.price_var.set(0.0)
            self.level_var.set(0)
            self.done_var.set(0)

    def _on_heading_click(self, column: str):
        asc = self._sort_state.get(column, True)
        self._sort_by(column, asc)
        self._sort_state[column] = not asc

    def _sort_by(self, column: str, ascending: bool = True):
        # build sortable list
        items = [(self.tree.set(k, column), k) for k in self.tree.get_children("")]

        def try_num(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return val.lower() if isinstance(val, str) else val

        items = [(try_num(v), k) for (v, k) in items]
        items.sort(reverse=not ascending, key=lambda t: t[0])

        for index, (_val, k) in enumerate(items):
            self.tree.move(k, "", index)

        # update headings to show arrow
        for col in ("title", "category", "price", "total", "level", "done"):
            base = "Count" if col == "done" else col.capitalize()
            arrow = ""
            if col == column:
                arrow = " ▲" if ascending else " ▼"
            self.tree.heading(col, text=base + arrow,
                              command=lambda c=col: self._on_heading_click(c))

    def _inc_count(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.askokcancel("Increment", "Select a task to increment")
            return
        iid = sel[0]
        tid = int(iid)
        try:
            curr = int(self.tree.set(iid, "done"))
        except (ValueError, TypeError):
            curr = 0
        new = curr + 1
        self.db.update_task(tid, done=new)
        self._load_tasks()
        try:
            self.tree.selection_set(iid)
            self.tree.see(iid)
        except (tk.TclError, KeyError):
            pass
        self.done_var.set(new)

    def _dec_count(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.askokcancel("Decrement", "Select a task to decrement")
            return
        iid = sel[0]
        tid = int(iid)
        try:
            curr = int(self.tree.set(iid, "done"))
        except (ValueError, TypeError):
            curr = 0
        if curr <= 0:
            return
        new = curr - 1
        self.db.update_task(tid, done=new)
        self._load_tasks()
        try:
            self.tree.selection_set(iid)
            self.tree.see(iid)
        except (tk.TclError, KeyError):
            pass
        self.done_var.set(new)

    def _add_task(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required")
            return
        category = self.category_var.get().strip()
        try:
            price = float(self.price_var.get())
        except (ValueError, TypeError):
            price = 0.0
        level = int(self.level_var.get() or 0)
        done = int(self.done_var.get() or 0)
        self.db.add_task(title, category, price, level, done)
        self._populate_category_filter()
        self._load_tasks()
        self._clear_form()

    def _edit_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.askokcancel("Edit", "Select a task to edit")
            return
        iid = sel[0]
        tid = int(iid)
        try:
            price = float(self.price_var.get())
        except (ValueError, TypeError):
            price = 0.0
        self.db.update_task(tid, title=self.title_var.get().strip(),
                            category=self.category_var.get().strip(),
                            price=price, level=int(self.level_var.get() or 0),
                            done=int(self.done_var.get() or 0))
        self._populate_category_filter()
        self._load_tasks()

    def _delete_task(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.askokcancel("Delete", "Select a task to delete")
            return
        iid = sel[0]
        tid = int(iid)
        if messagebox.askyesno("Delete", "Delete selected task?"):
            self.db.delete_task(tid)
            self._populate_category_filter()
            self._load_tasks()

    def _clear_form(self):
        self.title_var.set("")
        self.category_var.set("")
        self.price_var.set(0.0)
        self.level_var.set(0)
        self.done_var.set(0)

    def _show_chart(self):
        """Show a scatter plot of Price vs Count for each task,
        annotating points with task titles."""

        tasks = self.db.list_tasks()
        if not tasks:
            messagebox.showinfo("No data", "No tasks available to plot.")
            return
        # collect and sort tasks by price (ascending) so the y-axis is ordered
        rows = []
        for t in tasks:
            try:
                price = float(t.get('price') or 0.0)
            except (ValueError, TypeError):
                price = 0.0
            try:
                cnt = int(t.get('done') or 0)
            except (ValueError, TypeError):
                cnt = 0
            title = str(t.get('title') or '')
            rows.append((price, cnt, title))

        # sort rows by price so cheaper tasks appear at the top (lower y index)
        rows.sort(key=lambda r: r[0])
        prices = [r[0] for r in rows]
        counts = [r[1] for r in rows]
        titles = [r[2] for r in rows]

        # horizontal layout: x = price, y = task index (labels on y-axis)
        y = list(range(len(titles)))
        plt.figure(figsize=(10, max(6, len(titles) * 0.4)))

        # Decide whether to use a log scale: requires positive prices and sufficient spread
        positive_prices = [p for p in prices if p > 0]
        use_log = False
        if positive_prices:
            max_p = max(positive_prices)
            min_p = min(positive_prices)
            if min_p <= 0:
                min_p = min([p for p in positive_prices if p > 0]) if positive_prices else 0.1
            # if spread is large (e.g., >20x), prefer log scale to de-cluster
            if max_p / min_p > 20:
                use_log = True

        # For plotting, clamp non-positive prices to a small positive value when using log
        if use_log:
            min_positive = min(positive_prices) if positive_prices else 0.1
            clamp = max(min_positive * 0.1, 0.001)
            plot_prices = [p if p > 0 else clamp for p in prices]
            plt.xscale('log')
        else:
            plot_prices = prices

        # draw subtle horizontal lines across the plot for each task row
        if plot_prices:
            xmin = min(plot_prices)
            xmax = max(plot_prices)
        else:
            xmin, xmax = 0.0, 1.0
        # ensure a non-zero span
        if xmin == xmax:
            if use_log:
                xmin = xmin * 0.5 if xmin > 0 else 0.001
                xmax = xmax * 1.5 if xmax > 0 else 1.0
            else:
                xmin = xmin - 1
                xmax = xmax + 1
        try:
            plt.hlines(y, xmin, xmax, colors='#e6e6e6', linewidth=0.8, zorder=0)
        except (ValueError, TypeError):
            # fallback to enabling y-grid if hlines fails for any reason
            plt.grid(axis='y', alpha=0.15)

        plt.scatter(plot_prices, y, color='#4C72B0', s=80, zorder=2)

        # annotate each point with the count (number of times done) to the right
        for xi, yi, cnt in zip(plot_prices, y, counts):
            # offset annotation slightly to the right; for log scale use multiplicative offset
            if use_log:
                text_x = xi * 1.08
            else:
                text_x = (xi + (0.02 * (max(plot_prices) - min(plot_prices)) if
                                plot_prices and max(plot_prices) != min(plot_prices) else 0.5))
            plt.text(text_x, yi, str(cnt), fontsize=8, va='center', ha='left', color='#222222')

        # set y-axis labels to task titles
        plt.yticks(y, [t if len(t) <= 60 else t[:57] + '...' for t in titles])

        plt.title('Price vs Task Count')
        plt.xlabel('Price')
        plt.ylabel('Task')
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # when running as script, create the themed window inside the app (preferred)
    app = TaskManagerApp()
    try:
        app.root.mainloop()
    except AttributeError:
        # fallback to plain Tk
        root = tk.Tk()
        app = TaskManagerApp(root)
        root.mainloop()
