"""
Personal Finance Management System
====================================
Task 02 – Cantilever Internship
Tech: Python 3, Tkinter (GUI), SQLite (Storage), Matplotlib (Charts)

Features
--------
• Dashboard – KPI cards + 4 embedded charts
• Transactions tab – add / delete income & expense entries
• Budget tab    – set category budgets & track usage
• Charts tab    – 5 dedicated, full-size chart views
• Reports tab   – monthly summary table
• Pre-loaded dummy data for immediate visualisation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, os, datetime, random

# ── optional matplotlib ───────────────────────
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─────────────────────────────────────────────
# Palette
# ─────────────────────────────────────────────
BG       = "#0D1117"
CARD     = "#161B22"
CARD2    = "#1C2230"
INPUT    = "#21262D"
BORDER   = "#30363D"
ACCENT   = "#7C3AED"
ACCENT2  = "#A78BFA"
GREEN    = "#22C55E"
RED      = "#EF4444"
AMBER    = "#F59E0B"
BLUE     = "#3B82F6"
CYAN     = "#06B6D4"
PINK     = "#EC4899"
TEXT     = "#E6EDF3"
MUTED    = "#8B949E"
FF       = "Segoe UI"

# chart colour wheel
COLORS_CHART = ["#7C3AED","#22C55E","#3B82F6","#F59E0B",
                "#EC4899","#06B6D4","#EF4444","#A78BFA",
                "#34D399","#FB923C"]

CATEGORIES = ["Salary","Freelance","Investment","Rental",   # income
              "Food","Rent","Transport","Utilities",
              "Entertainment","Shopping","Health","Education","Other"]

INCOME_CATS  = {"Salary","Freelance","Investment","Rental"}
EXPENSE_CATS = set(CATEGORIES) - INCOME_CATS

# ─────────────────────────────────────────────
# Database Layer
# ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "finance.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT    NOT NULL,
            type      TEXT    NOT NULL,   -- 'income' | 'expense'
            category  TEXT    NOT NULL,
            desc      TEXT,
            amount    REAL    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            category  TEXT    UNIQUE NOT NULL,
            amount    REAL    NOT NULL
        );
        """)

def seed_dummy_data():
    """Insert 6 months of realistic dummy transactions if table is empty."""
    with get_conn() as con:
        if con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] > 0:
            return   # already seeded

        today = datetime.date.today()
        rows = []

        monthly_income = [
            ("Salary",    55000),
            ("Freelance", lambda: random.randint(5000, 18000)),
        ]

        expense_templates = [
            ("Rent",         22000, 1),
            ("Food",         lambda: random.randint(3000, 8000), 4),
            ("Transport",    lambda: random.randint(800,  2500), 3),
            ("Utilities",    lambda: random.randint(1500, 3500), 1),
            ("Entertainment",lambda: random.randint(500,  3000), 2),
            ("Shopping",     lambda: random.randint(1000, 6000), 2),
            ("Health",       lambda: random.randint(500,  4000), 1),
            ("Education",    lambda: random.randint(2000, 5000), 1),
        ]

        for m in range(5, -1, -1):
            month_start = (today.replace(day=1) - datetime.timedelta(days=m*28))
            year, month = month_start.year, month_start.month

            def rdate():
                day = random.randint(1, 28)
                return datetime.date(year, month, day).isoformat()

            # Income
            for cat, amt in monthly_income:
                a = amt() if callable(amt) else amt
                rows.append((rdate(), "income", cat, f"{cat} – {month_start.strftime('%b %Y')}", a))

            # Investment some months
            if random.random() > 0.4:
                rows.append((rdate(), "income", "Investment",
                             "Dividend / returns", random.randint(1000, 8000)))

            # Expenses
            for cat, amt_fn, freq in expense_templates:
                for _ in range(freq):
                    a = amt_fn() if callable(amt_fn) else amt_fn
                    rows.append((rdate(), "expense", cat, f"{cat} payment", a))

        con.executemany(
            "INSERT INTO transactions (date,type,category,desc,amount) VALUES (?,?,?,?,?)",
            rows)

        # Default budgets
        budgets = [
            ("Food", 8000), ("Rent", 22000), ("Transport", 3000),
            ("Utilities", 4000), ("Entertainment", 4000),
            ("Shopping", 7000), ("Health", 5000), ("Education", 6000),
        ]
        con.executemany(
            "INSERT OR IGNORE INTO budgets (category,amount) VALUES (?,?)", budgets)

# ─────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────
def q_totals():
    with get_conn() as con:
        income  = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income'").fetchone()[0]
        expense = con.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense'").fetchone()[0]
    return income, expense

def q_by_category(ttype):
    with get_conn() as con:
        rows = con.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE type=? GROUP BY category ORDER BY 2 DESC",
            (ttype,)).fetchall()
    return rows

def q_monthly(ttype):
    with get_conn() as con:
        rows = con.execute("""
            SELECT strftime('%Y-%m', date) as ym, SUM(amount)
            FROM transactions WHERE type=?
            GROUP BY ym ORDER BY ym
        """, (ttype,)).fetchall()
    return rows

def q_recent(n=50):
    with get_conn() as con:
        return con.execute(
            "SELECT id,date,type,category,desc,amount FROM transactions ORDER BY date DESC LIMIT ?",
            (n,)).fetchall()

def q_budgets():
    with get_conn() as con:
        return con.execute("SELECT category,amount FROM budgets").fetchall()

def q_spent_by_cat():
    with get_conn() as con:
        rows = con.execute(
            "SELECT category,SUM(amount) FROM transactions WHERE type='expense' GROUP BY category"
        ).fetchall()
    return dict(rows)

def q_all_for_table(ttype=None, month=None):
    sql = "SELECT id,date,type,category,desc,amount FROM transactions WHERE 1=1"
    params = []
    if ttype:
        sql += " AND type=?"; params.append(ttype)
    if month:
        sql += " AND strftime('%Y-%m',date)=?"; params.append(month)
    sql += " ORDER BY date DESC"
    with get_conn() as con:
        return con.execute(sql, params).fetchall()

def insert_transaction(date, ttype, category, desc, amount):
    with get_conn() as con:
        con.execute(
            "INSERT INTO transactions (date,type,category,desc,amount) VALUES (?,?,?,?,?)",
            (date, ttype, category, desc, amount))

def delete_transaction(tid):
    with get_conn() as con:
        con.execute("DELETE FROM transactions WHERE id=?", (tid,))

def upsert_budget(category, amount):
    with get_conn() as con:
        con.execute(
            "INSERT INTO budgets (category,amount) VALUES (?,?) ON CONFLICT(category) DO UPDATE SET amount=?",
            (category, amount, amount))

# ─────────────────────────────────────────────
# Reusable Widgets
# ─────────────────────────────────────────────
def make_card(parent, **kw):
    f = tk.Frame(parent, bg=CARD, bd=0,
                 highlightthickness=1, highlightbackground=BORDER, **kw)
    return f

def lbl(parent, text, size=11, bold=False, color=TEXT, anchor="w", **kw):
    return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                    font=(FF, size, "bold" if bold else "normal"),
                    anchor=anchor, **kw)

def btn(parent, text, cmd, color=ACCENT, hov="#6D28D9", w=140, h=36):
    fr = tk.Frame(parent, bg=color, cursor="hand2", width=w, height=h)
    fr.pack_propagate(False)
    lb = tk.Label(fr, text=text, bg=color, fg=TEXT,
                  font=(FF, 10, "bold"), cursor="hand2")
    lb.pack(expand=True)
    for ww in (fr, lb):
        ww.bind("<Enter>",    lambda _, f=fr, l=lb: (f.config(bg=hov), l.config(bg=hov)))
        ww.bind("<Leave>",    lambda _, f=fr, l=lb: (f.config(bg=color), l.config(bg=color)))
        ww.bind("<Button-1>", lambda _: cmd())
    return fr

def kpi_card(parent, title, value, color, icon):
    c = make_card(parent)
    tk.Label(c, text=icon, bg=CARD, fg=color,
             font=(FF, 22)).pack(anchor="w", padx=16, pady=(14,0))
    lbl(c, title, 9, color=MUTED).pack(anchor="w", padx=16)
    lbl(c, value, 20, bold=True, color=color).pack(anchor="w", padx=16, pady=(0,14))
    return c

# ─────────────────────────────────────────────
# Main App
# ─────────────────────────────────────────────
class FinanceApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("💰  Personal Finance Manager")
        self.geometry("1280x780")
        self.minsize(1000, 660)
        self.configure(bg=BG)
        self.resizable(True, True)
        self._center()
        self._build_ui()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1280) // 2
        y = (self.winfo_screenheight() - 780)  // 2
        self.geometry(f"1280x780+{x}+{y}")

    # ── top-level layout ──────────────────────
    def _build_ui(self):
        self._build_topbar()
        self._build_sidebar()
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._pages = {}
        for name, builder in [
            ("Dashboard",    self._page_dashboard),
            ("Transactions", self._page_transactions),
            ("Budget",       self._page_budget),
            ("Charts",       self._page_charts),
            ("Reports",      self._page_reports),
        ]:
            p = tk.Frame(self._content, bg=BG)
            p.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[name] = p
            builder(p)

        self._show_page("Dashboard")

    # ── Top bar ───────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self, bg=ACCENT, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        lbl(bar, "💰  Personal Finance Manager", 15, bold=True,
            color=TEXT).pack(side="left", padx=20, pady=10)
        now = datetime.datetime.now().strftime("%d %b %Y  |  %H:%M")
        lbl(bar, now, 10, color="#C4B5FD").pack(side="right", padx=20)

    # ── Sidebar nav ───────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self, bg=CARD, width=190)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        lbl(sb, "  NAVIGATION", 8, color=MUTED).pack(anchor="w", pady=(18,6), padx=10)

        nav_items = [
            ("🏠", "Dashboard"),
            ("💳", "Transactions"),
            ("🎯", "Budget"),
            ("📊", "Charts"),
            ("📋", "Reports"),
        ]
        self._nav_btns = {}
        for icon, name in nav_items:
            f = tk.Frame(sb, bg=CARD, cursor="hand2", height=44)
            f.pack(fill="x", padx=8, pady=2)
            f.pack_propagate(False)

            inner = tk.Label(f, text=f"  {icon}  {name}",
                             bg=CARD, fg=TEXT,
                             font=(FF, 11), anchor="w",
                             cursor="hand2")
            inner.pack(fill="both", expand=True, padx=4)

            def _click(n=name, fr=f, lb=inner):
                self._show_page(n)

            f.bind("<Button-1>",  lambda e, fn=_click: fn())
            inner.bind("<Button-1>", lambda e, fn=_click: fn())
            f.bind("<Enter>",  lambda e, fr=f, lb=inner: (fr.config(bg=BG_HOVER()), lb.config(bg=BG_HOVER())))
            f.bind("<Leave>",  lambda e, fr=f, lb=inner, n=name: self._nav_reset(fr, lb, n))

            self._nav_btns[name] = (f, inner)

    def _show_page(self, name):
        for n, (f, lb) in self._nav_btns.items():
            active = (n == name)
            bg = ACCENT if active else CARD
            fg = TEXT   if active else MUTED
            f.config(bg=bg); lb.config(bg=bg, fg=fg)
        self._pages[name].lift()
        # Refresh dynamic pages
        if name == "Dashboard":    self._refresh_dashboard()
        if name == "Transactions": self._refresh_tx()
        if name == "Budget":       self._refresh_budget()
        if name == "Charts":       self._refresh_charts()
        if name == "Reports":      self._refresh_reports()

    def _nav_reset(self, fr, lb, name):
        active = lb["fg"] == TEXT and fr["bg"] == ACCENT
        if not active:
            fr.config(bg=CARD); lb.config(bg=CARD, fg=MUTED)

    # ═══════════════════════════════════════════
    # DASHBOARD
    # ═══════════════════════════════════════════
    def _page_dashboard(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        # KPI row
        self._kpi_row = tk.Frame(p, bg=BG)
        self._kpi_row.pack(fill="x", padx=20, pady=(16, 10))

        # Chart area
        self._dash_chart_frame = tk.Frame(p, bg=BG)
        self._dash_chart_frame.pack(fill="both", expand=True, padx=20, pady=(0,16))
        self._dash_chart_frame.columnconfigure((0,1), weight=1)
        self._dash_chart_frame.rowconfigure(0, weight=1)

    def _refresh_dashboard(self):
        # KPIs
        for w in self._kpi_row.winfo_children(): w.destroy()
        income, expense = q_totals()
        balance = income - expense
        savings_rate = (balance / income * 100) if income else 0

        kpis = [
            ("Total Income",  f"₹{income:,.0f}",      GREEN,  "📈"),
            ("Total Expense", f"₹{expense:,.0f}",     RED,    "📉"),
            ("Net Balance",   f"₹{balance:,.0f}",     ACCENT2,"🏦"),
            ("Savings Rate",  f"{savings_rate:.1f}%", AMBER,  "💹"),
        ]
        for i, (t, v, c, ic) in enumerate(kpis):
            card = kpi_card(self._kpi_row, t, v, c, ic)
            card.pack(side="left", fill="x", expand=True,
                      padx=(0 if i == 0 else 10, 0))

        if not HAS_MPL:
            lbl(self._dash_chart_frame,
                "Install matplotlib for charts:  pip install matplotlib",
                12, color=AMBER).grid(row=0, column=0, columnspan=2)
            return

        for w in self._dash_chart_frame.winfo_children(): w.destroy()

        plt.style.use("dark_background")

        # ── Chart 1: Monthly Income vs Expense (bar)
        c1 = make_card(self._dash_chart_frame)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        lbl(c1, "Monthly Income vs Expense", 11, bold=True).pack(anchor="w", padx=12, pady=(10,0))
        fig1 = Figure(figsize=(5, 3.2), dpi=90, facecolor=CARD)
        ax1 = fig1.add_subplot(111, facecolor=CARD)
        inc_m  = dict(q_monthly("income"))
        exp_m  = dict(q_monthly("expense"))
        months = sorted(set(inc_m)|set(exp_m))[-6:]
        x = range(len(months))
        w_ = 0.35
        bars1 = ax1.bar([i-w_/2 for i in x], [inc_m.get(m,0) for m in months], w_, color=GREEN, alpha=0.85, label="Income")
        bars2 = ax1.bar([i+w_/2 for i in x], [exp_m.get(m,0) for m in months], w_, color=RED,   alpha=0.85, label="Expense")
        ax1.set_xticks(list(x))
        ax1.set_xticklabels([m[5:] for m in months], color=MUTED, fontsize=8)
        ax1.tick_params(colors=MUTED, labelsize=8)
        ax1.spines[:].set_color(BORDER)
        ax1.legend(facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"₹{v/1000:.0f}k"))
        fig1.tight_layout(pad=1.0)
        FigureCanvasTkAgg(fig1, c1).get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4,8))

        # ── Chart 2: Expense breakdown (pie)
        c2 = make_card(self._dash_chart_frame)
        c2.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        lbl(c2, "Expense by Category", 11, bold=True).pack(anchor="w", padx=12, pady=(10,0))
        fig2 = Figure(figsize=(5, 3.2), dpi=90, facecolor=CARD)
        ax2 = fig2.add_subplot(111, facecolor=CARD)
        exp_cat = q_by_category("expense")
        if exp_cat:
            labels = [r[0] for r in exp_cat]
            sizes  = [r[1] for r in exp_cat]
            colors = COLORS_CHART[:len(labels)]
            wedges, texts, autotexts = ax2.pie(
                sizes, labels=None, colors=colors,
                autopct="%1.1f%%", pctdistance=0.75,
                startangle=140, wedgeprops=dict(width=0.55))
            for at in autotexts: at.set(color=TEXT, fontsize=7)
            ax2.legend(wedges, labels, loc="lower center",
                       facecolor=CARD, edgecolor=BORDER,
                       labelcolor=TEXT, fontsize=7,
                       ncol=3, bbox_to_anchor=(0.5,-0.12))
        fig2.tight_layout(pad=0.5)
        FigureCanvasTkAgg(fig2, c2).get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(4,8))

    # ═══════════════════════════════════════════
    # TRANSACTIONS
    # ═══════════════════════════════════════════
    def _page_transactions(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        # Form
        form = make_card(p)
        form.pack(fill="x", padx=20, pady=(16,10))
        for i in range(6): form.columnconfigure(i, weight=1)

        def fld(col, label, widget_fn):
            tk.Label(form, text=label, bg=CARD, fg=MUTED,
                     font=(FF,9)).grid(row=0, column=col, sticky="w", padx=(12,4), pady=(10,2))
            w = widget_fn()
            w.grid(row=1, column=col, sticky="ew", padx=(12,4), pady=(0,12), ipady=5)
            return w

        # Date
        self._tx_date = tk.StringVar(value=datetime.date.today().isoformat())
        fld(0, "Date", lambda: tk.Entry(form, textvariable=self._tx_date,
                                        bg=INPUT, fg=TEXT, insertbackground=ACCENT,
                                        relief="flat", font=(FF,10),
                                        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT))

        # Type
        self._tx_type = tk.StringVar(value="expense")
        type_cb = ttk.Combobox(form, textvariable=self._tx_type,
                               values=["income","expense"], state="readonly",
                               font=(FF,10))
        type_cb.grid(row=1, column=1, sticky="ew", padx=(12,4), pady=(0,12), ipady=5)
        tk.Label(form, text="Type", bg=CARD, fg=MUTED, font=(FF,9)
                 ).grid(row=0, column=1, sticky="w", padx=(12,4), pady=(10,2))

        # Category
        self._tx_cat = tk.StringVar(value="Food")
        cat_cb = ttk.Combobox(form, textvariable=self._tx_cat,
                              values=sorted(CATEGORIES), state="readonly",
                              font=(FF,10))
        cat_cb.grid(row=1, column=2, sticky="ew", padx=(12,4), pady=(0,12), ipady=5)
        tk.Label(form, text="Category", bg=CARD, fg=MUTED, font=(FF,9)
                 ).grid(row=0, column=2, sticky="w", padx=(12,4), pady=(10,2))

        # Description
        self._tx_desc = tk.StringVar()
        fld(3, "Description", lambda: tk.Entry(form, textvariable=self._tx_desc,
                                               bg=INPUT, fg=TEXT, insertbackground=ACCENT,
                                               relief="flat", font=(FF,10),
                                               highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT))

        # Amount
        self._tx_amt = tk.StringVar()
        fld(4, "Amount (₹)", lambda: tk.Entry(form, textvariable=self._tx_amt,
                                              bg=INPUT, fg=TEXT, insertbackground=ACCENT,
                                              relief="flat", font=(FF,10),
                                              highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT))

        # Add button
        b = btn(form, "➕  Add", self._add_tx, w=110, h=36)
        tk.Label(form, text=" ", bg=CARD, font=(FF,9)
                 ).grid(row=0, column=5, padx=8)
        b.grid(row=1, column=5, padx=(8,12), pady=(0,12))

        # Table
        table_frame = make_card(p)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0,16))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        cols = ("ID","Date","Type","Category","Description","Amount")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=CARD, foreground=TEXT,
                         fieldbackground=CARD, rowheight=30,
                         font=(FF, 10))
        style.configure("Dark.Treeview.Heading",
                         background=INPUT, foreground=ACCENT2,
                         font=(FF, 10, "bold"))
        style.map("Dark.Treeview", background=[("selected", ACCENT)])

        self._tx_tree = ttk.Treeview(table_frame, columns=cols,
                                      show="headings", style="Dark.Treeview",
                                      selectmode="browse")
        widths = [50, 90, 80, 100, 260, 100]
        for c, w_ in zip(cols, widths):
            self._tx_tree.heading(c, text=c)
            self._tx_tree.column(c, width=w_, anchor="center" if c != "Description" else "w")

        sb_y = ttk.Scrollbar(table_frame, orient="vertical",   command=self._tx_tree.yview)
        self._tx_tree.configure(yscrollcommand=sb_y.set)

        self._tx_tree.grid(row=0, column=0, sticky="nsew", padx=(8,0), pady=8)
        sb_y.grid(row=0, column=1, sticky="ns", pady=8, padx=(0,4))

        # Delete
        del_btn = btn(table_frame, "🗑  Delete Selected", self._del_tx,
                      color=RED, hov="#B91C1C", w=180, h=34)
        del_btn.grid(row=1, column=0, padx=8, pady=(0,8), sticky="w")

    def _add_tx(self):
        try:
            amt = float(self._tx_amt.get().replace(",",""))
            assert amt > 0
        except:
            messagebox.showerror("Error", "Enter a valid positive amount."); return
        insert_transaction(self._tx_date.get(), self._tx_type.get(),
                           self._tx_cat.get(), self._tx_desc.get(), amt)
        self._tx_amt.set("")
        self._tx_desc.set("")
        self._refresh_tx()

    def _del_tx(self):
        sel = self._tx_tree.selection()
        if not sel:
            messagebox.showinfo("Info","Select a row first."); return
        tid = self._tx_tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Delete",f"Delete transaction #{tid}?"):
            delete_transaction(tid)
            self._refresh_tx()

    def _refresh_tx(self):
        if not hasattr(self, "_tx_tree"): return
        for row in self._tx_tree.get_children():
            self._tx_tree.delete(row)
        for r in q_recent(100):
            tag = "inc" if r[2]=="income" else "exp"
            self._tx_tree.insert("", "end", values=r, tags=(tag,))
        self._tx_tree.tag_configure("inc", foreground=GREEN)
        self._tx_tree.tag_configure("exp", foreground="#FDA4AF")

    # ═══════════════════════════════════════════
    # BUDGET
    # ═══════════════════════════════════════════
    def _page_budget(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        # Set budget form
        form = make_card(p)
        form.pack(fill="x", padx=20, pady=(16,10))
        for i in range(3): form.columnconfigure(i, weight=1)

        tk.Label(form, text="Category", bg=CARD, fg=MUTED, font=(FF,9)
                 ).grid(row=0, column=0, sticky="w", padx=12, pady=(10,2))
        self._bud_cat = tk.StringVar(value="Food")
        cb = ttk.Combobox(form, textvariable=self._bud_cat,
                          values=sorted(EXPENSE_CATS), state="readonly", font=(FF,10))
        cb.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,12), ipady=5)

        tk.Label(form, text="Budget Amount (₹)", bg=CARD, fg=MUTED, font=(FF,9)
                 ).grid(row=0, column=1, sticky="w", padx=12, pady=(10,2))
        self._bud_amt = tk.StringVar()
        tk.Entry(form, textvariable=self._bud_amt, bg=INPUT, fg=TEXT,
                 insertbackground=ACCENT, relief="flat", font=(FF,10),
                 highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
                 ).grid(row=1, column=1, sticky="ew", padx=12, pady=(0,12), ipady=5)

        b = btn(form, "💾  Set Budget", self._set_budget, w=140, h=36)
        tk.Label(form, text=" ", bg=CARD, font=(FF,9)
                 ).grid(row=0, column=2, padx=8)
        b.grid(row=1, column=2, padx=12, pady=(0,12), sticky="w")

        # Budget bars frame (scrollable)
        self._bud_canvas_frame = make_card(p)
        self._bud_canvas_frame.pack(fill="both", expand=True, padx=20, pady=(0,16))
        self._bud_canvas_frame.columnconfigure(0, weight=1)
        self._bud_canvas_frame.rowconfigure(0, weight=1)

        if HAS_MPL:
            self._bud_fig_frame = tk.Frame(self._bud_canvas_frame, bg=CARD)
            self._bud_fig_frame.grid(row=0, column=0, sticky="nsew")

    def _set_budget(self):
        try:
            amt = float(self._bud_amt.get().replace(",",""))
            assert amt > 0
        except:
            messagebox.showerror("Error","Enter valid amount."); return
        upsert_budget(self._bud_cat.get(), amt)
        self._bud_amt.set("")
        self._refresh_budget()

    def _refresh_budget(self):
        if not hasattr(self, "_bud_fig_frame"): return
        if not HAS_MPL: return
        for w in self._bud_fig_frame.winfo_children(): w.destroy()

        budgets = dict(q_budgets())
        spent   = q_spent_by_cat()
        cats    = sorted(budgets.keys())
        if not cats: return

        fig = Figure(figsize=(10, max(3, len(cats)*0.7)), dpi=90, facecolor=CARD)
        ax  = fig.add_subplot(111, facecolor=CARD)

        budg_vals  = [budgets[c] for c in cats]
        spent_vals = [spent.get(c, 0) for c in cats]
        y = range(len(cats))

        ax.barh(list(y), budg_vals, 0.55, color=BLUE,   alpha=0.3, label="Budget")
        ax.barh(list(y), spent_vals, 0.55, color=lambda i=0: RED if spent_vals[i]>budg_vals[i] else GREEN,
                alpha=0.85, label="Spent")

        # Colour spent bars individually
        for patch, sv, bv in zip(ax.patches[len(cats):], spent_vals, budg_vals):
            patch.set_facecolor(RED if sv > bv else GREEN)

        ax.set_yticks(list(y))
        ax.set_yticklabels(cats, color=TEXT, fontsize=9)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.spines[:].set_color(BORDER)
        ax.set_xlabel("Amount (₹)", color=MUTED, fontsize=8)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"₹{v/1000:.0f}k"))
        ax.legend(facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)
        ax.set_title("Budget vs Actual Spending", color=TEXT, fontsize=11, pad=10)
        fig.tight_layout(pad=1.2)

        canvas = FigureCanvasTkAgg(fig, self._bud_fig_frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ═══════════════════════════════════════════
    # CHARTS (5 dedicated charts)
    # ═══════════════════════════════════════════
    def _page_charts(self, p):
        # Tab bar at top
        self._chart_tab_var = tk.StringVar(value="Line")
        tab_row = tk.Frame(p, bg=BG)
        tab_row.pack(fill="x", padx=20, pady=(14,0))

        self._chart_tabs = {}
        for name in ["Line","Pie","Bar","Donut","Scatter"]:
            f = tk.Frame(tab_row, bg=CARD, cursor="hand2",
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", padx=(0,4))
            lb = tk.Label(f, text=name, bg=CARD, fg=MUTED,
                          font=(FF,10,"bold"), padx=16, pady=8, cursor="hand2")
            lb.pack()
            for ww in (f, lb):
                ww.bind("<Button-1>", lambda _, n=name: self._switch_chart(n))
            self._chart_tabs[name] = (f, lb)

        # Chart container
        self._chart_container = make_card(p)
        self._chart_container.pack(fill="both", expand=True,
                                   padx=20, pady=(8,16))
        self._chart_container.columnconfigure(0, weight=1)
        self._chart_container.rowconfigure(0, weight=1)

    def _switch_chart(self, name):
        self._chart_tab_var.set(name)
        for n, (f, lb) in self._chart_tabs.items():
            active = n == name
            f.config(bg=ACCENT if active else CARD)
            lb.config(bg=ACCENT if active else CARD,
                      fg=TEXT   if active else MUTED)
        self._draw_chart(name)

    def _refresh_charts(self):
        if not hasattr(self, "_chart_tab_var"): return
        current = self._chart_tab_var.get() or "Line"
        self._switch_chart(current)

    def _draw_chart(self, chart_type):
        for w in self._chart_container.winfo_children(): w.destroy()
        if not HAS_MPL:
            lbl(self._chart_container,
                "matplotlib not installed. Run:  pip install matplotlib",
                12, color=AMBER).pack(padx=20, pady=40)
            return

        plt.style.use("dark_background")
        fig = Figure(figsize=(10, 5.5), dpi=90, facecolor=CARD)

        if chart_type == "Line":
            ax = fig.add_subplot(111, facecolor=CARD)
            inc_m = dict(q_monthly("income"))
            exp_m = dict(q_monthly("expense"))
            months = sorted(set(inc_m)|set(exp_m))
            x = range(len(months))
            iv = [inc_m.get(m,0) for m in months]
            ev = [exp_m.get(m,0) for m in months]
            ax.plot(list(x), iv, color=GREEN,  marker="o", lw=2.5, label="Income",  ms=6)
            ax.plot(list(x), ev, color=RED,    marker="s", lw=2.5, label="Expense", ms=6)
            ax.fill_between(list(x), iv, ev, alpha=0.08, color=ACCENT2)
            ax.set_xticks(list(x))
            ax.set_xticklabels([m[5:] for m in months], color=MUTED, fontsize=9)
            ax.tick_params(colors=MUTED)
            ax.spines[:].set_color(BORDER)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"₹{v/1000:.0f}k"))
            ax.legend(facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
            ax.set_title("Income vs Expense — Monthly Trend (Line)", color=TEXT, fontsize=12, pad=12)
            ax.grid(axis="y", color=BORDER, alpha=0.5)

        elif chart_type == "Pie":
            ax = fig.add_subplot(111, facecolor=CARD)
            data = q_by_category("expense")
            if data:
                labels, sizes = zip(*data)
                wedges, texts, autotexts = ax.pie(
                    sizes, labels=labels,
                    colors=COLORS_CHART[:len(labels)],
                    autopct="%1.1f%%", startangle=140,
                    textprops={"color": TEXT, "fontsize": 9},
                    pctdistance=0.82)
                for at in autotexts: at.set(fontsize=8)
            ax.set_title("Expense Distribution — Pie Chart", color=TEXT, fontsize=12, pad=12)

        elif chart_type == "Bar":
            ax = fig.add_subplot(111, facecolor=CARD)
            data = q_by_category("income") + q_by_category("expense")
            cats_all = [r[0] for r in data]
            amts_all = [r[1] for r in data]
            colors_ = [GREEN if c in INCOME_CATS else RED for c in cats_all]
            bars = ax.bar(cats_all, amts_all, color=colors_, alpha=0.85, width=0.6)
            ax.set_xticklabels(cats_all, rotation=35, ha="right", color=MUTED, fontsize=8)
            ax.tick_params(colors=MUTED)
            ax.spines[:].set_color(BORDER)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"₹{v/1000:.0f}k"))
            ax.set_title("Income & Expense by Category — Bar Chart", color=TEXT, fontsize=12, pad=12)
            ax.grid(axis="y", color=BORDER, alpha=0.5)
            p_inc = mpatches.Patch(color=GREEN, label="Income")
            p_exp = mpatches.Patch(color=RED,   label="Expense")
            ax.legend(handles=[p_inc, p_exp], facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)

        elif chart_type == "Donut":
            ax = fig.add_subplot(111, facecolor=CARD)
            inc, exp = q_totals()
            balance = max(inc - exp, 0)
            sizes  = [exp, balance]
            labels = ["Expenses", "Savings"]
            colors_ = [RED, GREEN]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors_,
                autopct="%1.1f%%", startangle=90,
                wedgeprops=dict(width=0.5),
                textprops={"color": TEXT, "fontsize": 11},
                pctdistance=0.75)
            for at in autotexts: at.set(fontsize=10, fontweight="bold")
            ax.text(0, 0, f"₹{inc:,.0f}\nIncome",
                    ha="center", va="center", color=TEXT,
                    fontsize=11, fontweight="bold")
            ax.set_title("Savings vs Expenses — Donut Chart", color=TEXT, fontsize=12, pad=12)

        elif chart_type == "Scatter":
            ax = fig.add_subplot(111, facecolor=CARD)
            with get_conn() as con:
                rows = con.execute(
                    "SELECT date, amount, type FROM transactions ORDER BY date"
                ).fetchall()
            if rows:
                import matplotlib.dates as mdates
                dates_inc = [datetime.datetime.strptime(r[0], "%Y-%m-%d") for r in rows if r[2]=="income"]
                amts_inc  = [r[1] for r in rows if r[2]=="income"]
                dates_exp = [datetime.datetime.strptime(r[0], "%Y-%m-%d") for r in rows if r[2]=="expense"]
                amts_exp  = [r[1] for r in rows if r[2]=="expense"]
                ax.scatter(dates_inc, amts_inc, color=GREEN, alpha=0.7, s=60, label="Income", zorder=3)
                ax.scatter(dates_exp, amts_exp, color=RED,   alpha=0.7, s=60, label="Expense", zorder=3)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                fig.autofmt_xdate(rotation=30)
            ax.tick_params(colors=MUTED)
            ax.spines[:].set_color(BORDER)
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"₹{v/1000:.0f}k"))
            ax.legend(facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, fontsize=9)
            ax.set_title("Transaction Amounts over Time — Scatter Plot", color=TEXT, fontsize=12, pad=12)
            ax.grid(color=BORDER, alpha=0.4)

        fig.tight_layout(pad=1.2)
        canvas = FigureCanvasTkAgg(fig, self._chart_container)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    # ═══════════════════════════════════════════
    # REPORTS
    # ═══════════════════════════════════════════
    def _page_reports(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)

        lbl(p, "  Monthly Summary", 14, bold=True).pack(anchor="w", padx=20, pady=(16,6))

        cols = ("Month","Income","Expenses","Net","Transactions")
        self._rep_tree = ttk.Treeview(p, columns=cols, show="headings",
                                       style="Dark.Treeview", height=20)
        widths2 = [120, 140, 140, 140, 120]
        for c, w_ in zip(cols, widths2):
            self._rep_tree.heading(c, text=c)
            self._rep_tree.column(c, width=w_, anchor="center")
        self._rep_tree.pack(fill="both", expand=True, padx=20, pady=(0,16))

    def _refresh_reports(self):
        if not hasattr(self,"_rep_tree"): return
        for r in self._rep_tree.get_children(): self._rep_tree.delete(r)
        with get_conn() as con:
            months = [r[0] for r in con.execute(
                "SELECT DISTINCT strftime('%Y-%m',date) FROM transactions ORDER BY 1"
            ).fetchall()]
        for m in months:
            with get_conn() as con:
                inc = con.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income' AND strftime('%Y-%m',date)=?", (m,)
                ).fetchone()[0]
                exp = con.execute(
                    "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense' AND strftime('%Y-%m',date)=?", (m,)
                ).fetchone()[0]
                cnt = con.execute(
                    "SELECT COUNT(*) FROM transactions WHERE strftime('%Y-%m',date)=?", (m,)
                ).fetchone()[0]
            net = inc - exp
            tag = "pos" if net >= 0 else "neg"
            self._rep_tree.insert("", "end", values=(
                m, f"₹{inc:,.0f}", f"₹{exp:,.0f}", f"₹{net:,.0f}", cnt
            ), tags=(tag,))
        self._rep_tree.tag_configure("pos", foreground=GREEN)
        self._rep_tree.tag_configure("neg", foreground=RED)


# ─────────────────────────────────────────────
# Patch hover helper
# ─────────────────────────────────────────────
def BG_HOVER():
    return "#1F2937"

# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    seed_dummy_data()
    app = FinanceApp()
    app.mainloop()
