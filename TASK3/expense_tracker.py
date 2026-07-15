"""
Expense Tracker - Task 3
A GUI application to visualize and manage expenses using Tkinter, SQLite, and Matplotlib.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import csv
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from collections import defaultdict

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────

DB_FILE = "expenses.db"

CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Travel",
               "Health", "Entertainment", "Education", "Others"]

CATEGORY_COLORS = {
    "Food":          "#FF6B6B",
    "Transport":     "#4ECDC4",
    "Shopping":      "#45B7D1",
    "Bills":         "#96CEB4",
    "Travel":        "#FFEAA7",
    "Health":        "#DDA0DD",
    "Entertainment": "#F0A500",
    "Education":     "#74B9FF",
    "Others":        "#A29BFE",
}

DUMMY_DATA = [
    ("2026-06-01",  450,  "Food",          "Grocery Store",        "Monthly groceries"),
    ("2026-06-02",  120,  "Transport",     "Uber Ride",            "Office commute"),
    ("2026-06-03",  2500, "Shopping",      "Amazon Order",         "Electronics"),
    ("2026-06-04",  800,  "Bills",         "Electricity Bill",     "June electricity"),
    ("2026-06-05",  3500, "Travel",        "Flight Ticket",        "Mumbai trip"),
    ("2026-06-07",  200,  "Health",        "Pharmacy",             "Medicines"),
    ("2026-06-08",  350,  "Entertainment", "Movie Tickets",        "Weekend fun"),
    ("2026-06-09",  150,  "Food",          "Restaurant Dinner",    "Family dinner"),
    ("2026-06-10",  500,  "Education",     "Online Course",        "Python course"),
    ("2026-06-11",  75,   "Transport",     "Metro Pass",           "Weekly pass"),
    ("2026-06-12",  600,  "Shopping",      "Clothing",             "New shirt & pants"),
    ("2026-06-13",  1200, "Bills",         "Internet Bill",        "Quarterly payment"),
    ("2026-06-14",  220,  "Food",          "Swiggy Order",         "Pizza night"),
    ("2026-06-15",  400,  "Health",        "Doctor Consultation",  "General checkup"),
    ("2026-06-16",  180,  "Entertainment", "Netflix Subscription", "Monthly plan"),
    ("2026-06-17",  2200, "Travel",        "Hotel Booking",        "2-night stay"),
    ("2026-06-18",  300,  "Food",          "Bakery",               "Weekend binge"),
    ("2026-06-19",  90,   "Transport",     "Auto Rickshaw",        "Local travel"),
    ("2026-06-20",  750,  "Shopping",      "Grocery + Veggies",    "Weekly stock"),
    ("2026-06-21",  500,  "Bills",         "Gas Cylinder",         "LPG refill"),
    ("2026-06-22",  1000, "Education",     "Book Purchase",        "Coding books"),
    ("2026-06-23",  650,  "Entertainment", "Concert Ticket",       "Live music"),
    ("2026-06-24",  280,  "Food",          "Cafe Outing",          "Coffee & snacks"),
    ("2026-06-25",  4000, "Travel",        "Train Ticket",         "Goa trip"),
    ("2026-06-26",  110,  "Transport",     "Petrol",               "Bike refuel"),
    ("2026-06-27",  850,  "Health",        "Gym Membership",       "Monthly fee"),
    ("2026-06-28",  400,  "Shopping",      "Footwear",             "Sneakers"),
    ("2026-06-29",  320,  "Food",          "Zepto Groceries",      "Fresh produce"),
    ("2026-06-30",  900,  "Bills",         "Mobile Recharge",      "Annual plan"),
    ("2026-07-01",  560,  "Food",          "Restaurant Lunch",     "Team lunch"),
    ("2026-07-02",  200,  "Transport",     "Cab to Airport",       "Business trip"),
    ("2026-07-03",  1500, "Shopping",      "Kitchen Appliance",    "Electric kettle"),
    ("2026-07-04",  700,  "Bills",         "Water Bill",           "Quarter payment"),
    ("2026-07-05",  2800, "Travel",        "Resort Booking",       "Weekend getaway"),
    ("2026-07-06",  130,  "Health",        "Vitamins",             "Supplements"),
    ("2026-07-07",  250,  "Entertainment", "Board Game",           "Game night"),
    ("2026-07-08",  420,  "Food",          "Birthday Cake",        "Celebration"),
    ("2026-07-09",  800,  "Education",     "Workshop Fee",         "Design workshop"),
    ("2026-07-10",  95,   "Transport",     "Bus Ticket",           "Day trip"),
    ("2026-07-11",  1100, "Shopping",      "Gadget Accessories",   "Phone case etc."),
    ("2026-07-12",  380,  "Bills",         "Streaming Services",   "Hotstar + Prime"),
    ("2026-07-13",  310,  "Food",          "Homemade supplies",    "Baking ingredients"),
    ("2026-07-14",  500,  "Health",        "Dental Visit",         "Cleaning"),
    ("2026-07-15",  680,  "Entertainment", "Bowling + Dinner",     "Friends outing"),
]

# =============================================================
#  DATABASE LAYER
# =============================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT    NOT NULL,
            notes       TEXT
        )
    """)
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM expenses")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO expenses (date, amount, category, description, notes) VALUES (?,?,?,?,?)",
            DUMMY_DATA
        )
        conn.commit()
    conn.close()


def fetch_all(filters=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    query  = "SELECT id, date, amount, category, description, notes FROM expenses"
    params = []
    clauses = []
    if filters:
        if filters.get("category") and filters["category"] != "All":
            clauses.append("category = ?")
            params.append(filters["category"])
        if filters.get("from_date"):
            clauses.append("date >= ?")
            params.append(filters["from_date"])
        if filters.get("to_date"):
            clauses.append("date <= ?")
            params.append(filters["to_date"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_expense(date, amount, category, description, notes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (date, amount, category, description, notes) VALUES (?,?,?,?,?)",
        (date, amount, category, description, notes)
    )
    conn.commit()
    conn.close()


def update_expense(eid, date, amount, category, description, notes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "UPDATE expenses SET date=?, amount=?, category=?, description=?, notes=? WHERE id=?",
        (date, amount, category, description, notes, eid)
    )
    conn.commit()
    conn.close()


def delete_expense(eid):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (eid,))
    conn.commit()
    conn.close()


def fetch_summary():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY SUM(amount) DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_monthly_trend():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses GROUP BY month ORDER BY month
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# =============================================================
#  GUI APPLICATION
# =============================================================

class ExpenseTrackerApp(tk.Tk):
    BG    = "#1A1A2E"
    PANEL = "#16213E"
    ACC   = "#0F3460"
    HL    = "#E94560"
    FG    = "#EAEAEA"

    def __init__(self):
        super().__init__()
        self.title("Expense Tracker")
        self.geometry("1340x820")
        self.minsize(1100, 680)
        self.configure(bg=self.BG)
        self.resizable(True, True)
        self._setup_styles()
        self._build_header()
        self._build_notebook()
        self._load_expenses()

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        BG, PANEL, ACC, HL, FG = self.BG, self.PANEL, self.ACC, self.HL, self.FG
        s.configure("TNotebook",         background=BG,    borderwidth=0)
        s.configure("TNotebook.Tab",     background=ACC,   foreground=FG,
                     padding=[18, 8],    font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", HL)],
              foreground=[("selected", "#FFFFFF")])
        s.configure("Treeview",          background=PANEL, foreground=FG,
                     fieldbackground=PANEL, rowheight=28, font=("Segoe UI", 9))
        s.configure("Treeview.Heading",  background=ACC,   foreground=HL,
                     font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", HL)],
              foreground=[("selected", "#FFFFFF")])
        s.configure("TScrollbar",        background=ACC,   troughcolor=PANEL)
        s.configure("TCombobox",         fieldbackground=PANEL, background=ACC,
                     foreground=FG,      arrowcolor=HL)
        s.configure("TLabel",            background=BG,    foreground=FG,
                     font=("Segoe UI", 10))
        s.configure("TFrame",            background=BG)

    def _build_header(self):
        hdr = tk.Frame(self, bg=self.ACC, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  EXPENSE TRACKER",
                 bg=self.ACC, fg=self.HL,
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=24, pady=14)
        self.total_var = tk.StringVar(value="Total: Rs 0.00")
        tk.Label(hdr, textvariable=self.total_var, bg=self.ACC, fg=self.FG,
                 font=("Segoe UI", 13)).pack(side="right", padx=30)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        self.tab_dash    = ttk.Frame(self.nb)
        self.tab_list    = ttk.Frame(self.nb)
        self.tab_add     = ttk.Frame(self.nb)
        self.tab_charts  = ttk.Frame(self.nb)
        self.nb.add(self.tab_dash,   text="  Dashboard")
        self.nb.add(self.tab_list,   text="  All Expenses")
        self.nb.add(self.tab_add,    text="  Add Expense")
        self.nb.add(self.tab_charts, text="  Charts")
        self._build_dashboard()
        self._build_expense_list()
        self._build_add_form()
        self._build_charts_tab()

    # ── Dashboard ─────────────────────────────────────────────
    def _build_dashboard(self):
        frame = self.tab_dash
        card_row = tk.Frame(frame, bg=self.BG)
        card_row.pack(fill="x", padx=14, pady=14)
        self.card_vars = {}
        card_defs = [
            ("Total Spent",   "total",   "#E94560"),
            ("Transactions",  "count",   "#0F3460"),
            ("Top Category",  "top_cat", "#4ECDC4"),
            ("This Month",    "monthly", "#F0A500"),
        ]
        for i, (lbl, key, color) in enumerate(card_defs):
            card = tk.Frame(card_row, bg=color)
            card.grid(row=0, column=i, padx=8, sticky="nsew")
            card_row.columnconfigure(i, weight=1)
            tk.Label(card, text=lbl, bg=color, fg="white",
                     font=("Segoe UI", 10, "bold")).pack(pady=(14, 2), padx=18)
            v = tk.StringVar(value="--")
            self.card_vars[key] = v
            tk.Label(card, textvariable=v, bg=color, fg="white",
                     font=("Segoe UI", 15, "bold")).pack(pady=(0, 14), padx=18)
        chart_frame = tk.Frame(frame, bg=self.PANEL)
        chart_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.dash_fig    = Figure(figsize=(12, 4), facecolor=self.PANEL)
        self.dash_canvas = FigureCanvasTkAgg(self.dash_fig, master=chart_frame)
        self.dash_canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── All Expenses ──────────────────────────────────────────
    def _build_expense_list(self):
        frame = self.tab_list
        fbar = tk.Frame(frame, bg=self.ACC, pady=6)
        fbar.pack(fill="x", padx=10, pady=(8, 0))

        def lbl(t):
            return tk.Label(fbar, text=t, bg=self.ACC, fg=self.FG,
                            font=("Segoe UI", 10))

        lbl("Category:").pack(side="left", padx=(10, 3))
        self.filter_cat = ttk.Combobox(fbar, values=["All"] + CATEGORIES,
                                        width=13, state="readonly")
        self.filter_cat.set("All")
        self.filter_cat.pack(side="left", padx=3)
        lbl("From:").pack(side="left", padx=(12, 3))
        self.filter_from = tk.Entry(fbar, bg=self.PANEL, fg=self.FG,
                                     insertbackground=self.FG, width=12,
                                     font=("Segoe UI", 9), relief="flat", bd=4)
        self.filter_from.insert(0, "2026-06-01")
        self.filter_from.pack(side="left", padx=3)
        lbl("To:").pack(side="left", padx=(8, 3))
        self.filter_to = tk.Entry(fbar, bg=self.PANEL, fg=self.FG,
                                   insertbackground=self.FG, width=12,
                                   font=("Segoe UI", 9), relief="flat", bd=4)
        self.filter_to.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.filter_to.pack(side="left", padx=3)

        tk.Button(fbar, text="Filter", bg=self.HL, fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._apply_filter,
                  padx=10, pady=3).pack(side="left", padx=10)
        tk.Button(fbar, text="Reset", bg="#4ECDC4", fg="#1A1A2E",
                  font=("Segoe UI", 9, "bold"), relief="flat",
                  cursor="hand2", command=self._reset_filter,
                  padx=10, pady=3).pack(side="left", padx=3)

        cols = ("ID", "Date", "Amount (Rs)", "Category", "Description", "Notes")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings",
                                   selectmode="browse")
        widths  = [50, 100, 110, 115, 210, 220]
        anchors = ["center", "center", "center", "center", "w", "w"]
        for col, w, anc in zip(cols, widths, anchors):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anc)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

        act_row = tk.Frame(frame, bg=self.BG)
        act_row.pack(fill="x", padx=10, pady=(0, 8))
        for text, cmd, bg, fg in [
            ("Edit",       self._edit_expense,   "#F0A500", "white"),
            ("Delete",     self._delete_expense,  self.HL,   "white"),
            ("Export CSV", self._export_csv,      "#4ECDC4", "#1A1A2E"),
        ]:
            tk.Button(act_row, text=text, bg=bg, fg=fg,
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      cursor="hand2", command=cmd,
                      padx=12, pady=5).pack(side="left", padx=6)
        self.status_var = tk.StringVar(value="")
        tk.Label(act_row, textvariable=self.status_var, bg=self.BG,
                 fg="#AAAAAA", font=("Segoe UI", 9)).pack(side="right", padx=10)

    # ── Add Expense ───────────────────────────────────────────
    def _build_add_form(self):
        outer = tk.Frame(self.tab_add, bg=self.BG)
        outer.pack(fill="both", expand=True)
        wrap = tk.Frame(outer, bg=self.PANEL, bd=2, relief="flat")
        wrap.place(relx=0.5, rely=0.5, anchor="center", width=540)
        tk.Label(wrap, text="Add New Expense", bg=self.PANEL, fg=self.HL,
                 font=("Segoe UI", 16, "bold")).pack(pady=(24, 12))
        flds = tk.Frame(wrap, bg=self.PANEL)
        flds.pack(padx=40, pady=4, fill="x")
        self.form_vars = {}
        form_fields = [
            ("Date (YYYY-MM-DD)", "entry"),
            ("Amount (Rs)",       "entry"),
            ("Category",          "combo"),
            ("Description",       "entry"),
            ("Notes",             "entry"),
        ]
        for i, (lbl_text, kind) in enumerate(form_fields):
            tk.Label(flds, text=lbl_text, bg=self.PANEL, fg="#AAAAAA",
                     font=("Segoe UI", 10)).grid(row=i, column=0,
                                                  sticky="w", pady=7)
            if kind == "combo":
                w = ttk.Combobox(flds, values=CATEGORIES, width=28, state="readonly")
                w.set("Food")
            else:
                w = tk.Entry(flds, bg=self.ACC, fg=self.FG,
                              insertbackground=self.FG,
                              font=("Segoe UI", 10), width=30,
                              relief="flat", bd=4)
                if "Date" in lbl_text:
                    w.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
            w.grid(row=i, column=1, padx=(14, 0), pady=7, sticky="ew")
            self.form_vars[lbl_text] = w
        tk.Button(wrap, text="Add Expense",
                  bg=self.HL, fg="white",
                  font=("Segoe UI", 12, "bold"), relief="flat",
                  cursor="hand2", command=self._submit_expense,
                  pady=10).pack(fill="x", padx=40, pady=(18, 30))

    # ── Charts Tab ────────────────────────────────────────────
    def _build_charts_tab(self):
        self.chart_fig    = Figure(figsize=(13, 5.5), facecolor=self.BG)
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master=self.tab_charts)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True,
                                                padx=10, pady=10)

    # ── Data Load ─────────────────────────────────────────────
    def _load_expenses(self, filters=None):
        rows = fetch_all(filters)
        self._populate_tree(rows)
        self._update_cards(rows)
        self._draw_dashboard_charts()
        self._draw_main_charts()

    def _populate_tree(self, rows):
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))
        self.tree.tag_configure("even", background="#16213E")
        self.tree.tag_configure("odd",  background="#1A1A2E")

    def _update_cards(self, rows):
        total   = sum(r[2] for r in rows)
        count   = len(rows)
        summary = fetch_summary()
        top_cat = summary[0][0] if summary else "--"
        today   = datetime.date.today()
        month   = today.strftime("%Y-%m")
        monthly = sum(r[2] for r in fetch_all() if r[1].startswith(month))
        self.total_var.set(f"Total Spent:  Rs {total:,.2f}")
        self.card_vars["total"].set(f"Rs {total:,.2f}")
        self.card_vars["count"].set(str(count))
        self.card_vars["top_cat"].set(top_cat)
        self.card_vars["monthly"].set(f"Rs {monthly:,.2f}")
        self.status_var.set(f"{count} record(s) shown")

    # ── Dashboard Charts ──────────────────────────────────────
    def _draw_dashboard_charts(self):
        self.dash_fig.clear()
        summary = fetch_summary()
        if not summary:
            return
        labels  = [r[0] for r in summary]
        amounts = [r[1] for r in summary]
        colors  = [CATEGORY_COLORS.get(l, "#888") for l in labels]
        gs = gridspec.GridSpec(1, 2, figure=self.dash_fig,
                                wspace=0.38, left=0.04, right=0.97,
                                top=0.88, bottom=0.10)
        ax1 = self.dash_fig.add_subplot(gs[0])
        wedges, _, autotexts = ax1.pie(
            amounts, colors=colors, autopct="%1.1f%%",
            startangle=140, pctdistance=0.75,
            wedgeprops=dict(width=0.55, edgecolor=self.PANEL, linewidth=1.5)
        )
        for at in autotexts:
            at.set_color("white"); at.set_fontsize(7.5)
        ax1.set_facecolor(self.PANEL)
        ax1.set_title("Spending by Category", color=self.HL,
                       fontsize=11, fontweight="bold", pad=10)
        patches = [mpatches.Patch(color=colors[i],
                                   label=f"{labels[i]}  Rs {amounts[i]:,.0f}")
                   for i in range(len(labels))]
        ax1.legend(handles=patches, loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    fontsize=7.5, framealpha=0, labelcolor="white")
        ax2 = self.dash_fig.add_subplot(gs[1])
        trend      = fetch_monthly_trend()
        months     = [r[0] for r in trend]
        totals     = [r[1] for r in trend]
        cur_m      = datetime.date.today().strftime("%Y-%m")
        bar_colors = [self.HL if m == cur_m else "#4ECDC4" for m in months]
        bars = ax2.bar(months, totals, color=bar_colors, width=0.5, zorder=3)
        ax2.set_facecolor(self.PANEL)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.spines[:].set_visible(False)
        ax2.yaxis.grid(True, color="#2A2A4A", zorder=0)
        ax2.set_title("Monthly Spending", color=self.HL,
                       fontsize=11, fontweight="bold")
        for bar, val in zip(bars, totals):
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(totals) * 0.015,
                     f"Rs {val:,.0f}", ha="center", va="bottom",
                     color="white", fontsize=7.5)
        self.dash_fig.patch.set_facecolor(self.PANEL)
        self.dash_canvas.draw()

    # ── Full Charts ───────────────────────────────────────────
    def _draw_main_charts(self):
        self.chart_fig.clear()
        summary  = fetch_summary()
        trend    = fetch_monthly_trend()
        all_rows = fetch_all()
        if not summary:
            return
        labels  = [r[0] for r in summary]
        amounts = [r[1] for r in summary]
        colors  = [CATEGORY_COLORS.get(l, "#888") for l in labels]
        gs = gridspec.GridSpec(2, 2, figure=self.chart_fig,
                                hspace=0.48, wspace=0.38,
                                left=0.08, right=0.97,
                                top=0.93, bottom=0.10)
        ax1 = self.chart_fig.add_subplot(gs[0, 0])
        _, _, autotexts = ax1.pie(
            amounts, colors=colors, autopct="%1.1f%%",
            startangle=90, pctdistance=0.80,
            wedgeprops=dict(width=0.45, edgecolor=self.BG, linewidth=2)
        )
        for at in autotexts:
            at.set_color("white"); at.set_fontsize(7.5)
        ax1.set_title("Category Distribution", color=self.HL,
                       fontsize=10, fontweight="bold")
        ax1.set_facecolor(self.BG)
        ax2 = self.chart_fig.add_subplot(gs[0, 1])
        pairs = sorted(zip(amounts, labels, colors), reverse=True)
        s_amt, s_lbl, s_col = zip(*pairs)
        ax2.barh(s_lbl, s_amt, color=s_col, height=0.6)
        ax2.set_facecolor(self.BG)
        ax2.tick_params(colors="#AAAAAA", labelsize=8)
        ax2.spines[:].set_visible(False)
        ax2.xaxis.grid(True, color="#2A2A4A")
        ax2.set_title("Category Totals (Rs)", color=self.HL,
                       fontsize=10, fontweight="bold")
        ax2.tick_params(axis="y", labelcolor=self.FG)
        ax3 = self.chart_fig.add_subplot(gs[1, 0])
        months = [r[0] for r in trend]
        totals = [r[1] for r in trend]
        x = list(range(len(months)))
        ax3.plot(x, totals, color=self.HL, linewidth=2.5, marker="o",
                  markerfacecolor="#FFEAA7", markeredgecolor=self.HL,
                  markersize=7, zorder=3)
        ax3.fill_between(x, totals, alpha=0.15, color=self.HL)
        ax3.set_xticks(x)
        ax3.set_xticklabels(months, rotation=30, ha="right",
                             color="#AAAAAA", fontsize=8)
        ax3.set_facecolor(self.BG)
        ax3.tick_params(colors="#AAAAAA", labelsize=8)
        ax3.spines[:].set_visible(False)
        ax3.yaxis.grid(True, color="#2A2A4A")
        ax3.set_title("Monthly Trend (Rs)", color=self.HL,
                       fontsize=10, fontweight="bold")
        ax4 = self.chart_fig.add_subplot(gs[1, 1])
        cat_month = defaultdict(lambda: defaultdict(float))
        for row in all_rows:
            cat_month[row[1][:7]][row[3]] += row[2]
        all_months = sorted(cat_month.keys())
        bottom = [0.0] * len(all_months)
        for cat, color in CATEGORY_COLORS.items():
            vals = [cat_month[m].get(cat, 0) for m in all_months]
            if any(v > 0 for v in vals):
                ax4.bar(all_months, vals, bottom=bottom,
                         color=color, label=cat, width=0.6)
                bottom = [b + v for b, v in zip(bottom, vals)]
        ax4.set_facecolor(self.BG)
        ax4.tick_params(colors="#AAAAAA", labelsize=8)
        ax4.spines[:].set_visible(False)
        ax4.yaxis.grid(True, color="#2A2A4A")
        ax4.set_title("Stacked by Category / Month", color=self.HL,
                       fontsize=10, fontweight="bold")
        ax4.legend(fontsize=6.5, loc="upper left",
                    framealpha=0, labelcolor="white", ncol=2)
        self.chart_fig.patch.set_facecolor(self.BG)
        self.chart_canvas.draw()

    # ── Filters ───────────────────────────────────────────────
    def _apply_filter(self):
        self._load_expenses({
            "category":  self.filter_cat.get(),
            "from_date": self.filter_from.get().strip(),
            "to_date":   self.filter_to.get().strip(),
        })

    def _reset_filter(self):
        self.filter_cat.set("All")
        self.filter_from.delete(0, "end")
        self.filter_from.insert(0, "2026-06-01")
        self.filter_to.delete(0, "end")
        self.filter_to.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self._load_expenses()

    # ── Submit ────────────────────────────────────────────────
    def _submit_expense(self):
        date  = self.form_vars["Date (YYYY-MM-DD)"].get().strip()
        amt   = self.form_vars["Amount (Rs)"].get().strip()
        cat   = self.form_vars["Category"].get()
        desc  = self.form_vars["Description"].get().strip()
        notes = self.form_vars["Notes"].get().strip()
        if not all([date, amt, cat, desc]):
            messagebox.showwarning("Missing Fields",
                                    "Date, Amount, Category, and Description are required.")
            return
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
            amount = float(amt)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input",
                                  "Enter a valid date (YYYY-MM-DD) and a positive amount.")
            return
        insert_expense(date, amount, cat, desc, notes)
        messagebox.showinfo("Success", "Expense added successfully!")
        for key, w in self.form_vars.items():
            if isinstance(w, tk.Entry):
                w.delete(0, "end")
                if "Date" in key:
                    w.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.form_vars["Category"].set("Food")
        self._load_expenses()
        self.nb.select(self.tab_list)

    # ── Edit / Delete / Export ────────────────────────────────
    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a row first.")
            return None
        return self.tree.item(sel[0], "values")[0]

    def _edit_expense(self):
        eid = self._get_selected_id()
        if not eid:
            return
        vals = self.tree.item(self.tree.selection()[0], "values")
        dlg = tk.Toplevel(self)
        dlg.title("Edit Expense")
        dlg.geometry("460x380")
        dlg.configure(bg=self.PANEL)
        dlg.grab_set()
        tk.Label(dlg, text="Edit Expense", bg=self.PANEL, fg=self.HL,
                 font=("Segoe UI", 14, "bold")).pack(pady=(16, 10))
        frm = tk.Frame(dlg, bg=self.PANEL)
        frm.pack(padx=30, fill="x")
        labels_vals = [
            ("Date (YYYY-MM-DD)", vals[1]),
            ("Amount (Rs)",       vals[2]),
            ("Category",          vals[3]),
            ("Description",       vals[4]),
            ("Notes",             vals[5]),
        ]
        edit_vars = {}
        for i, (lbl_text, val) in enumerate(labels_vals):
            tk.Label(frm, text=lbl_text, bg=self.PANEL, fg="#AAAAAA",
                     font=("Segoe UI", 10)).grid(row=i, column=0,
                                                  sticky="w", pady=7)
            if lbl_text == "Category":
                w = ttk.Combobox(frm, values=CATEGORIES,
                                   width=24, state="readonly")
                w.set(val)
            else:
                w = tk.Entry(frm, bg=self.ACC, fg=self.FG,
                              insertbackground=self.FG,
                              font=("Segoe UI", 10), width=26,
                              relief="flat", bd=4)
                w.insert(0, val)
            w.grid(row=i, column=1, padx=(10, 0), pady=7)
            edit_vars[lbl_text] = w

        def _save():
            try:
                d  = edit_vars["Date (YYYY-MM-DD)"].get().strip()
                a  = float(edit_vars["Amount (Rs)"].get().strip())
                c  = edit_vars["Category"].get()
                de = edit_vars["Description"].get().strip()
                no = edit_vars["Notes"].get().strip()
                datetime.datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid", "Check date and amount.", parent=dlg)
                return
            update_expense(int(eid), d, a, c, de, no)
            dlg.destroy()
            self._load_expenses()

        tk.Button(dlg, text="Save Changes", bg=self.HL, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat",
                  cursor="hand2", command=_save,
                  pady=8).pack(fill="x", padx=30, pady=(14, 20))

    def _delete_expense(self):
        eid = self._get_selected_id()
        if not eid:
            return
        if messagebox.askyesno("Confirm Delete",
                                f"Permanently delete expense ID #{eid}?"):
            delete_expense(int(eid))
            self._load_expenses()

    def _export_csv(self):
        filename = f"expenses_export_{datetime.date.today()}.csv"
        rows = fetch_all()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Date", "Amount", "Category", "Description", "Notes"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Data saved to:\n{filename}")


# =============================================================
#  ENTRY POINT
# =============================================================

if __name__ == "__main__":
    init_db()
    app = ExpenseTrackerApp()
    app.mainloop()
