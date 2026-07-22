import json
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ------
# Config
# ------

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo_data.json")

DEFAULT_TASKS = [
    {"id": "wake",    "label": "Get up",         "type": "check"},
    {"id": "stretch", "label": "Stretch",         "type": "check"},
    {"id": "workout", "label": "Workout",         "type": "check"},
    {"id": "polish",  "label": "Revise Polish",   "type": "check"},
    {"id": "jobs",    "label": "Apply to jobs",   "type": "counter", "target": 3},
    {"id": "project", "label": "Work on project", "type": "check"},
]

BG      = "#2a3125"
CARD    = "#2b4228"
INK     = "#b39264"
INK_DIM = "#766b3e"
GOLD    = "#818c3c"
SAGE    = "#818c3c"
DANGER  = "#D97776"
LINE    = "#19270d"

FONT_DISPLAY = ("Georgia", 20, "bold")
FONT_BODY    = ("Segoe UI", 11)
FONT_MONO    = ("Courier New", 9)

BAR_COLOR = "#3A4172"  
MA_WINDOW = 10 


def moving_average(values, window=MA_WINDOW):
    result = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1):i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


# ----------
# Data layer
# ----------

def today_str():
    return date.today().isoformat()


def yesterday_str(d_str):
    d = date.fromisoformat(d_str)
    return (d - timedelta(days=1)).isoformat()


def pretty_date(d_str):
    return date.fromisoformat(d_str).strftime("%A, %B %d")


def new_task_id():
    return f"t{int(time.time() * 1000)}"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("tasks", [t.copy() for t in DEFAULT_TASKS])
    data.setdefault("logs", {})
    data.setdefault("streak", {"count": 0, "last_date": None})
    data["logs"].setdefault(today_str(), {"counted": False, "extras": []})
    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---
# App
# ---

class DailyRitualApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daily Ritual")
        self.geometry("420x680")
        self.configure(bg=BG)

        self.data = load_data()
        self.today = today_str()
        self.log = self.data["logs"][self.today]
        self.edit_mode = False
        self.new_task_type = tk.StringVar(value="check")

        self._build_ui()
        self.refresh()

    @property
    def tasks(self):
        return self.data["tasks"]

    @property
    def streak(self):
        return self.data["streak"]

    def task_done(self, t):
        if t["type"] == "counter":
            return self.log.get(t["id"], 0) >= t["target"]
        return bool(self.log.get(t["id"], False))

    def all_done(self):
        return len(self.tasks) > 0 and all(self.task_done(t) for t in self.tasks)

    def save(self):
        save_data(self.data)

    def _build_ui(self):
        pad = 18

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=pad, pady=(pad, 6))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        self.date_lbl = tk.Label(left, text="", bg=BG, fg=INK_DIM, font=FONT_MONO)
        self.date_lbl.pack(anchor="w")
        tk.Label(left, text="Today's Ritual", bg=BG, fg=INK, font=FONT_DISPLAY).pack(anchor="w")

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")
        self.streak_num_lbl = tk.Label(right, text="0", bg=BG, fg=GOLD, font=("Courier New", 18, "bold"))
        self.streak_num_lbl.pack(anchor="e")
        tk.Label(right, text="DAY STREAK", bg=BG, fg=INK_DIM, font=("Courier New", 8)).pack(anchor="e")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Ritual.Horizontal.TProgressbar", troughcolor=CARD, background=GOLD,
                         bordercolor=BG, lightcolor=GOLD, darkcolor=GOLD)
        self.progress = ttk.Progressbar(self, style="Ritual.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x", padx=pad, pady=(6, 2))
        self.progress_lbl = tk.Label(self, text="", bg=BG, fg=INK_DIM, font=FONT_MONO)
        self.progress_lbl.pack(pady=(0, 10))

        sec = tk.Frame(self, bg=BG)
        sec.pack(fill="x", padx=pad)
        tk.Label(sec, text="DAILY TASKS", bg=BG, fg=INK_DIM, font=FONT_MONO).pack(side="left")
        self.edit_btn = tk.Button(sec, text="Edit", command=self.toggle_edit, bg=BG, fg=INK_DIM,
                                   relief="solid", bd=1, font=FONT_MONO, padx=8, cursor="hand2")
        self.edit_btn.pack(side="right")
        self.stats_btn = tk.Button(sec, text="Stats", command=self.open_stats, bg=BG, fg=INK_DIM,
                                    relief="solid", bd=1, font=FONT_MONO, padx=8, cursor="hand2")
        self.stats_btn.pack(side="right", padx=(0, 6))

        self.tasks_frame = tk.Frame(self, bg=CARD)
        self.tasks_frame.pack(fill="x", padx=pad, pady=(6, 10))

        self.extras_label_head = tk.Label(self, text="ALSO TODAY", bg=BG, fg=INK_DIM, font=FONT_MONO)
        self.extras_frame = tk.Frame(self, bg=CARD)

        add_row = tk.Frame(self, bg=BG)
        add_row.pack(fill="x", padx=pad, pady=(4, 4))
        self.extra_entry = tk.Entry(add_row, bg=CARD, fg=INK, insertbackground=INK, relief="flat", font=FONT_BODY)
        self.extra_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.extra_entry.bind("<Return>", lambda e: self.add_extra())
        tk.Button(add_row, text="Add", command=self.add_extra, bg=GOLD, fg=BG, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, cursor="hand2").pack(side="left")

        tk.Label(self, text="Resets fresh each day. Streak counts a day when every task is done.",
                 bg=BG, fg=INK_DIM, font=("Courier New", 8), wraplength=380, justify="center").pack(pady=(6, 12))

    def refresh(self):
        self.date_lbl.config(text=pretty_date(self.today).upper())
        self.streak_num_lbl.config(text=str(self.streak["count"]))

        total = len(self.tasks)
        done_weight = 0.0
        for t in self.tasks:
            if t["type"] == "counter":
                done_weight += min(self.log.get(t["id"], 0) / t["target"], 1)
            else:
                done_weight += 1 if self.log.get(t["id"], False) else 0
        self.progress["value"] = (done_weight / total * 100) if total else 0
        done_count = sum(1 for t in self.tasks if self.task_done(t))
        self.progress_lbl.config(text=f"{done_count} of {total} done")

        self.edit_btn.config(text="Done" if self.edit_mode else "Edit",
                              fg=GOLD if self.edit_mode else INK_DIM)

        for w in self.tasks_frame.winfo_children():
            w.destroy()

        if not self.tasks:
            tk.Label(self.tasks_frame, text="No daily tasks yet.", bg=CARD, fg=INK_DIM,
                     font=FONT_BODY, pady=14).pack()
        else:
            for t in self.tasks:
                self._render_task_row(t)

        if self.edit_mode:
            self._render_add_task_row()

        self._render_extras()

    def _render_task_row(self, t):
        row = tk.Frame(self.tasks_frame, bg=CARD)
        row.pack(fill="x", padx=10, pady=8)

        if not self.edit_mode:
            done = self.task_done(t)
            cb = tk.Button(row, text=("\u2713" if done else ""), width=2,
                           bg=(SAGE if done else CARD), fg=BG, relief="solid", bd=1,
                           command=lambda t=t: self.on_task_click(t), cursor="hand2")
            cb.pack(side="left", padx=(0, 10))

            lbl = tk.Label(row, text=t["label"], bg=CARD, fg=(INK_DIM if done else INK),
                           font=("Segoe UI", 11, "overstrike" if done else "normal"), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)

            if t["type"] == "counter":
                counter = tk.Frame(row, bg=CARD)
                counter.pack(side="right")
                tk.Button(counter, text="-", width=2, command=lambda t=t: self.adjust_counter(t, -1),
                          bg=CARD, fg=INK, relief="solid", bd=1, cursor="hand2").pack(side="left")
                val = self.log.get(t["id"], 0)
                tk.Label(counter, text=f"{val}/{t['target']}", bg=CARD, fg=INK_DIM,
                         font=FONT_MONO, width=6).pack(side="left")
                tk.Button(counter, text="+", width=2, command=lambda t=t: self.adjust_counter(t, 1),
                          bg=CARD, fg=INK, relief="solid", bd=1, cursor="hand2").pack(side="left")
        else:
            entry = tk.Entry(row, bg=BG, fg=INK, insertbackground=INK, relief="flat", font=FONT_BODY)
            entry.insert(0, t["label"])
            entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 8))
            entry.bind("<FocusOut>", lambda e, t=t, en=entry: self.edit_label(t, en.get()))
            entry.bind("<Return>", lambda e, t=t, en=entry: self.edit_label(t, en.get()))

            tk.Label(row, text=t["type"], bg=CARD, fg=INK_DIM, font=("Courier New", 8)).pack(side="left", padx=6)

            if t["type"] == "counter":
                tgt = tk.Spinbox(row, from_=1, to=99, width=3, bg=BG, fg=INK, relief="flat", font=FONT_MONO)
                tgt.delete(0, "end")
                tgt.insert(0, str(t["target"]))
                tgt.pack(side="left", padx=6)
                tgt.bind("<FocusOut>", lambda e, t=t, sb=tgt: self.edit_target(t, sb.get()))

            tk.Button(row, text="\u2715", command=lambda t=t: self.delete_task(t), bg=CARD, fg=DANGER,
                      relief="flat", font=("Segoe UI", 11), cursor="hand2").pack(side="left", padx=(6, 0))

    def _render_add_task_row(self):
        row = tk.Frame(self.tasks_frame, bg=CARD)
        row.pack(fill="x", padx=10, pady=(10, 12))

        self.new_task_entry = tk.Entry(row, bg=BG, fg=INK, insertbackground=INK, relief="flat", font=FONT_BODY)
        self.new_task_entry.pack(fill="x", ipady=5, pady=(0, 6))
        self.new_task_entry.bind("<Return>", lambda e: self.add_task())

        controls = tk.Frame(row, bg=CARD)
        controls.pack(fill="x")

        tk.Radiobutton(controls, text="Checkbox", variable=self.new_task_type, value="check",
                       bg=CARD, fg=INK_DIM, selectcolor=BG, activebackground=CARD,
                       font=FONT_MONO, command=self.refresh).pack(side="left")
        tk.Radiobutton(controls, text="Counter", variable=self.new_task_type, value="counter",
                       bg=CARD, fg=INK_DIM, selectcolor=BG, activebackground=CARD,
                       font=FONT_MONO, command=self.refresh).pack(side="left", padx=(6, 0))

        self.new_task_target = None
        if self.new_task_type.get() == "counter":
            tk.Label(controls, text="target", bg=CARD, fg=INK_DIM, font=FONT_MONO).pack(side="left", padx=(10, 2))
            self.new_task_target = tk.Spinbox(controls, from_=1, to=99, width=3, bg=BG, fg=INK, relief="flat")
            self.new_task_target.pack(side="left")

        tk.Button(controls, text="Add Task", command=self.add_task, bg=GOLD, fg=BG,
                  relief="flat", font=("Segoe UI", 9, "bold"), padx=10, cursor="hand2").pack(side="right")

    def _render_extras(self):
        for w in self.extras_frame.winfo_children():
            w.destroy()

        if self.log["extras"]:
            self.extras_label_head.pack(fill="x", padx=18, pady=(0, 4))
            self.extras_frame.pack(fill="x", padx=18, pady=(0, 6))
            for i, ex in enumerate(self.log["extras"]):
                row = tk.Frame(self.extras_frame, bg=CARD)
                row.pack(fill="x", padx=10, pady=6)
                done = ex["done"]
                tk.Button(row, text=("\u2713" if done else ""), width=2,
                          bg=(SAGE if done else CARD), fg=BG, relief="solid", bd=1,
                          command=lambda i=i: self.toggle_extra(i), cursor="hand2").pack(side="left", padx=(0, 10))
                tk.Label(row, text=ex["label"], bg=CARD, fg=(INK_DIM if done else INK),
                         font=("Segoe UI", 10, "overstrike" if done else "normal"),
                         anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(row, text="\u2715", command=lambda i=i: self.delete_extra(i), bg=CARD, fg=DANGER,
                          relief="flat", font=("Segoe UI", 10), cursor="hand2").pack(side="right")
        else:
            self.extras_label_head.pack_forget()
            self.extras_frame.pack_forget()

    def toggle_edit(self):
        self.edit_mode = not self.edit_mode
        self.refresh()

    def on_task_click(self, t):
        if t["type"] == "counter":
            self.adjust_counter(t, t["target"] if not self.task_done(t) else -t["target"])
        else:
            self.log[t["id"]] = not self.log.get(t["id"], False)
            self.after_progress_change()

    def adjust_counter(self, t, delta):
        cur = self.log.get(t["id"], 0)
        self.log[t["id"]] = max(0, min(t["target"], cur + delta))
        self.after_progress_change()

    def after_progress_change(self):
        done = self.all_done()
        if done and not self.log.get("counted"):
            yest = yesterday_str(self.today)
            self.streak["count"] = self.streak["count"] + 1 if self.streak["last_date"] == yest else 1
            self.streak["last_date"] = self.today
            self.log["counted"] = True
        elif not done and self.log.get("counted"):
            if self.streak["last_date"] == self.today:
                self.streak["count"] = max(0, self.streak["count"] - 1)
                self.streak["last_date"] = yesterday_str(self.today) if self.streak["count"] > 0 else None
            self.log["counted"] = False
        self.save()
        self.refresh()

    def edit_label(self, t, val):
        t["label"] = val.strip() or "Untitled task"
        self.save()

    def edit_target(self, t, val):
        try:
            t["target"] = max(1, int(val))
        except ValueError:
            pass
        self.save()
        self.after_progress_change()

    def delete_task(self, t):
        self.data["tasks"] = [x for x in self.tasks if x["id"] != t["id"]]
        self.log.pop(t["id"], None)
        self.save()
        self.after_progress_change()

    def add_task(self):
        label = self.new_task_entry.get().strip()
        if not label:
            return
        task = {"id": new_task_id(), "label": label, "type": self.new_task_type.get()}
        if task["type"] == "counter":
            try:
                task["target"] = max(1, int(self.new_task_target.get()))
            except (ValueError, AttributeError, TypeError):
                task["target"] = 3
        self.data["tasks"].append(task)
        self.save()
        self.refresh()

    def add_extra(self):
        text = self.extra_entry.get().strip()
        if not text:
            return
        self.log["extras"].append({"label": text, "done": False})
        self.extra_entry.delete(0, "end")
        self.save()
        self.refresh()

    def toggle_extra(self, i):
        self.log["extras"][i]["done"] = not self.log["extras"][i]["done"]
        self.save()
        self.refresh()

    def delete_extra(self, i):
        self.log["extras"].pop(i)
        self.save()
        self.refresh()

    def _style_axis(self, ax, x, tick_labels):
        ax.set_facecolor(CARD)
        ax.tick_params(colors=INK_DIM, labelsize=7)
        for spine in ax.spines.values():
            spine.set_color(LINE)
        step = max(1, len(x) // 8)
        ax.set_xticks(x[::step])
        ax.set_xticklabels([tick_labels[i] for i in range(0, len(tick_labels), step)],
                            rotation=45, ha="right")

    def open_stats(self):
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showinfo("Stats", "Graphs need matplotlib. Install it with:\n\npip install matplotlib")
            return

        dates = sorted(self.data["logs"].keys())
        if len(dates) < 2:
            messagebox.showinfo("Stats", "Not enough history yet - keep using the app for a few days "
                                          "and check back.")
            return

        win = tk.Toplevel(self)
        win.title("Stats")
        win.geometry("640x800")
        win.configure(bg=BG)

        container = tk.Frame(win, bg=BG)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        x = list(range(len(dates)))
        tick_labels = [d[5:] for d in dates]  # MM-DD
        n_tasks = len(self.tasks)
        total_rows = n_tasks + 2

        fig = Figure(figsize=(6, 2.3 * total_rows), dpi=100)
        fig.patch.set_facecolor(BG)

        # one graph per daily task: 1/0 completion each day + 10-day moving average
        row = 1
        for t in self.tasks:
            ax = fig.add_subplot(total_rows, 1, row)
            series = []
            for d in dates:
                log = self.data["logs"][d]
                if t["type"] == "counter":
                    done = log.get(t["id"], 0) >= t["target"]
                else:
                    done = bool(log.get(t["id"], False))
                series.append(1 if done else 0)
            ax.bar(x, series, color=BAR_COLOR, width=0.7)
            ax.plot(x, moving_average(series), color=GOLD, linewidth=2)
            ax.set_ylim(-0.1, 1.1)
            ax.set_title(t["label"], color=INK, fontsize=10, loc="left")
            self._style_axis(ax, x, tick_labels)
            row += 1

        ax = fig.add_subplot(total_rows, 1, row)
        sums = []
        for d in dates:
            log = self.data["logs"][d]
            s = 0
            for t in self.tasks:
                if t["type"] == "counter":
                    s += 1 if log.get(t["id"], 0) >= t["target"] else 0
                else:
                    s += 1 if log.get(t["id"], False) else 0
            sums.append(s)
        ax.bar(x, sums, color=BAR_COLOR, width=0.7)
        ax.plot(x, moving_average(sums), color=SAGE, linewidth=2)
        ax.set_ylim(-0.3, max(sums + [1]) + 0.5)
        ax.set_title(f"All tasks completed per day (of {n_tasks})", color=INK, fontsize=10, loc="left")
        self._style_axis(ax, x, tick_labels)
        row += 1

        ax = fig.add_subplot(total_rows, 1, row)
        counts, rates = [], []
        for d in dates:
            extras = self.data["logs"][d].get("extras", [])
            c = len(extras)
            done = sum(1 for e in extras if e["done"])
            counts.append(c)
            rates.append(done / c if c else 0)
        ax2 = ax.twinx()
        ax.bar(x, counts, color=BAR_COLOR, width=0.7, label="count")
        ax2.plot(x, rates, color=GOLD, linewidth=2, label="completion rate")
        ax.set_ylim(-0.3, max(counts + [1]) + 0.5)
        ax2.set_ylim(-0.1, 1.1)
        ax2.tick_params(colors=INK_DIM, labelsize=7)
        for spine in ax2.spines.values():
            spine.set_color(LINE)
        ax.set_title("Extra tasks: count (bars) & completion rate (line)", color=INK, fontsize=10, loc="left")
        self._style_axis(ax, x, tick_labels)

        fig.tight_layout()
        canvas_widget = FigureCanvasTkAgg(fig, master=scroll_frame)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    app = DailyRitualApp()
    app.mainloop()
