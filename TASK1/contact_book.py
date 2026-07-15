"""
Contact Book Application
========================
A modern Contact Book built with Python Tkinter.
Data is persisted to a JSON file for storage.

Author  : Cantilever Internship – Task 01
Tech    : Python 3, Tkinter (GUI), JSON File I/O (Storage)
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
import re

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "contacts.json")

# Colour palette – dark modern theme
BG_DARK    = "#0F1117"
BG_CARD    = "#1A1D27"
BG_INPUT   = "#252836"
BG_HOVER   = "#2D3147"
ACCENT     = "#6C63FF"
ACCENT2    = "#A78BFA"
SUCCESS    = "#22C55E"
DANGER     = "#EF4444"
WARNING    = "#F59E0B"
TEXT_PRI   = "#F1F5F9"
TEXT_SEC   = "#94A3B8"
TEXT_MUTED = "#475569"
BORDER     = "#2E3347"

FONT_FAMILY = "Segoe UI"


# ─────────────────────────────────────────────
#  Data Layer
# ─────────────────────────────────────────────
class ContactStore:
    """Handles all JSON file I/O for contacts."""

    def __init__(self, path: str):
        self.path = path
        self._contacts: list[dict] = []
        self._load()

    # ── internal helpers ──────────────────────
    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._contacts = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._contacts = []
        else:
            self._contacts = []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._contacts, f, indent=2, ensure_ascii=False)

    # ── public API ────────────────────────────
    def all(self) -> list[dict]:
        return list(self._contacts)

    def search(self, query: str) -> list[dict]:
        q = query.lower()
        return [c for c in self._contacts
                if q in c.get("name", "").lower()
                or q in c.get("phone", "").lower()
                or q in c.get("email", "").lower()
                or q in c.get("group", "").lower()]

    def add(self, contact: dict) -> None:
        self._contacts.append(contact)
        self._save()

    def update(self, index: int, contact: dict) -> None:
        self._contacts[index] = contact
        self._save()

    def delete(self, index: int) -> None:
        self._contacts.pop(index)
        self._save()

    def get(self, index: int) -> dict:
        return self._contacts[index]

    def count(self) -> int:
        return len(self._contacts)


# ─────────────────────────────────────────────
#  UI Helpers
# ─────────────────────────────────────────────
def _make_button(parent, text, command, color=ACCENT,
                 hover_color=None, width=120, height=36, icon=""):
    hover_color = hover_color or color
    frame = tk.Frame(parent, bg=color, cursor="hand2",
                     bd=0, highlightthickness=0)
    frame.config(width=width, height=height)
    frame.pack_propagate(False)

    lbl = tk.Label(frame,
                   text=f"{icon}  {text}" if icon else text,
                   bg=color, fg=TEXT_PRI,
                   font=(FONT_FAMILY, 10, "bold"),
                   cursor="hand2")
    lbl.pack(expand=True, fill="both")

    # Hover effect
    def on_enter(_):
        frame.config(bg=hover_color)
        lbl.config(bg=hover_color)

    def on_leave(_):
        frame.config(bg=color)
        lbl.config(bg=color)

    for widget in (frame, lbl):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", lambda _: command())

    return frame


def _rounded_entry(parent, textvariable, placeholder="", show=""):
    """Returns a styled Entry widget."""
    entry = tk.Entry(parent,
                     textvariable=textvariable,
                     bg=BG_INPUT,
                     fg=TEXT_PRI,
                     insertbackground=ACCENT,
                     relief="flat",
                     font=(FONT_FAMILY, 11),
                     bd=0,
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACCENT,
                     show=show)

    if placeholder:
        entry.insert(0, placeholder)
        entry.config(fg=TEXT_MUTED)

        def on_focus_in(_):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg=TEXT_PRI)

        def on_focus_out(_):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg=TEXT_MUTED)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    return entry


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────
class ContactBookApp(tk.Tk):

    GROUPS = ["Family", "Friends", "Work", "Business", "Other"]

    def __init__(self):
        super().__init__()
        self.store = ContactStore(DATA_FILE)
        self._selected_index: int | None = None   # index in self.store.all()
        self._filtered: list[dict] = []

        self._build_window()
        self._build_ui()
        self._refresh_list()

    # ── Window setup ──────────────────────────
    def _build_window(self):
        self.title("📒  Contact Book")
        self.geometry("1000x680")
        self.minsize(850, 580)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Centre on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 1000) // 2
        y = (self.winfo_screenheight() - 680)  // 2
        self.geometry(f"1000x680+{x}+{y}")

    # ── Top-level layout ──────────────────────
    def _build_ui(self):
        self._build_header()

        content = tk.Frame(self, bg=BG_DARK)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._build_left_panel(content)
        self._build_right_panel(content)

    # ── Header ────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        title = tk.Label(hdr,
                         text="📒  Contact Book",
                         bg=ACCENT, fg=TEXT_PRI,
                         font=(FONT_FAMILY, 18, "bold"))
        title.pack(side="left", padx=24)

        self._stats_lbl = tk.Label(hdr,
                                   text="",
                                   bg=ACCENT, fg="#D4D0FF",
                                   font=(FONT_FAMILY, 10))
        self._stats_lbl.pack(side="right", padx=24)

    # ── Left panel – list & search ─────────────
    def _build_left_panel(self, parent):
        panel = tk.Frame(parent, bg=BG_CARD, bd=0)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=1)

        # Search bar
        search_frame = tk.Frame(panel, bg=BG_INPUT,
                                highlightthickness=1,
                                highlightbackground=BORDER,
                                highlightcolor=ACCENT)
        search_frame.grid(row=0, column=0, sticky="ew",
                          padx=12, pady=12)

        tk.Label(search_frame, text="🔍", bg=BG_INPUT,
                 font=(FONT_FAMILY, 12)).pack(side="left", padx=(8, 4))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)

        search_entry = tk.Entry(search_frame,
                                textvariable=self._search_var,
                                bg=BG_INPUT, fg=TEXT_PRI,
                                insertbackground=ACCENT,
                                relief="flat", bd=4,
                                font=(FONT_FAMILY, 11))
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.insert(0, "Search contacts…")
        search_entry.config(fg=TEXT_MUTED)

        def _sf_in(_):
            if search_entry.get() == "Search contacts…":
                search_entry.delete(0, "end")
                search_entry.config(fg=TEXT_PRI)

        def _sf_out(_):
            if not search_entry.get():
                search_entry.insert(0, "Search contacts…")
                search_entry.config(fg=TEXT_MUTED)

        search_entry.bind("<FocusIn>",  _sf_in)
        search_entry.bind("<FocusOut>", _sf_out)

        # Contact listbox
        list_frame = tk.Frame(panel, bg=BG_CARD)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self._listbox = tk.Listbox(list_frame,
                                   bg=BG_CARD,
                                   fg=TEXT_PRI,
                                   selectbackground=ACCENT,
                                   selectforeground=TEXT_PRI,
                                   activestyle="none",
                                   relief="flat",
                                   bd=0,
                                   highlightthickness=0,
                                   font=(FONT_FAMILY, 11),
                                   cursor="hand2",
                                   exportselection=False)
        self._listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(list_frame, orient="vertical",
                                 command=self._listbox.yview,
                                 bg=BG_CARD, troughcolor=BG_CARD,
                                 activebackground=ACCENT)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._listbox.config(yscrollcommand=scrollbar.set)
        self._listbox.bind("<<ListboxSelect>>", self._on_list_select)

        # New contact button
        btn = _make_button(panel, "＋  New Contact",
                           self._new_contact,
                           color=ACCENT,
                           hover_color="#7C74FF",
                           width=200, height=40)
        btn.grid(row=2, column=0, padx=12, pady=(0, 12))

    # ── Right panel – form ────────────────────
    def _build_right_panel(self, parent):
        self._right = tk.Frame(parent, bg=BG_CARD)
        self._right.grid(row=0, column=1, sticky="nsew")
        self._right.columnconfigure(0, weight=1)
        self._right.columnconfigure(1, weight=1)

        # ── form title
        self._form_title = tk.Label(self._right,
                                    text="Select a contact",
                                    bg=BG_CARD, fg=TEXT_PRI,
                                    font=(FONT_FAMILY, 16, "bold"),
                                    anchor="w")
        self._form_title.grid(row=0, column=0, columnspan=2,
                               padx=24, pady=(24, 4), sticky="ew")

        self._form_sub = tk.Label(self._right,
                                  text="or click ＋ New Contact to add one",
                                  bg=BG_CARD, fg=TEXT_SEC,
                                  font=(FONT_FAMILY, 10),
                                  anchor="w")
        self._form_sub.grid(row=1, column=0, columnspan=2,
                             padx=24, pady=(0, 16), sticky="ew")

        sep = tk.Frame(self._right, bg=BORDER, height=1)
        sep.grid(row=2, column=0, columnspan=2,
                 padx=24, sticky="ew", pady=(0, 20))

        # ── Avatar circle
        self._avatar_frame = tk.Frame(self._right, bg=BG_CARD)
        self._avatar_frame.grid(row=3, column=0, columnspan=2,
                                 padx=24, pady=(0, 20), sticky="w")

        self._avatar_canvas = tk.Canvas(self._avatar_frame,
                                        width=72, height=72,
                                        bg=BG_CARD, highlightthickness=0)
        self._avatar_canvas.pack(side="left")
        self._avatar_canvas.create_oval(4, 4, 68, 68,
                                        fill=ACCENT, outline="")
        self._avatar_lbl = self._avatar_canvas.create_text(
            36, 36, text="?",
            fill=TEXT_PRI,
            font=(FONT_FAMILY, 24, "bold"))

        avatar_info = tk.Frame(self._avatar_frame, bg=BG_CARD)
        avatar_info.pack(side="left", padx=16)
        self._av_name = tk.Label(avatar_info, text="No contact selected",
                                 bg=BG_CARD, fg=TEXT_PRI,
                                 font=(FONT_FAMILY, 13, "bold"))
        self._av_name.pack(anchor="w")
        self._av_group = tk.Label(avatar_info, text="",
                                  bg=BG_CARD, fg=ACCENT2,
                                  font=(FONT_FAMILY, 10))
        self._av_group.pack(anchor="w")

        # ── Form fields
        fields_info = [
            ("Full Name",    "name",    "👤", 4),
            ("Phone Number", "phone",   "📞", 5),
            ("Email",        "email",   "✉️",  6),
            ("Address",      "address", "🏠", 7),
        ]

        self._vars: dict[str, tk.StringVar] = {}
        for label, key, icon, row in fields_info:
            self._vars[key] = tk.StringVar()
            self._build_field(label, key, icon, row)

        # Group dropdown
        tk.Label(self._right, text="🏷️  Group",
                 bg=BG_CARD, fg=TEXT_SEC,
                 font=(FONT_FAMILY, 10)).grid(
            row=8, column=0, padx=24, sticky="w")

        self._vars["group"] = tk.StringVar(value="Other")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                         fieldbackground=BG_INPUT,
                         background=BG_INPUT,
                         foreground=TEXT_PRI,
                         selectbackground=ACCENT,
                         selectforeground=TEXT_PRI,
                         bordercolor=BORDER,
                         arrowcolor=ACCENT)

        combo = ttk.Combobox(self._right,
                             textvariable=self._vars["group"],
                             values=self.GROUPS,
                             state="readonly",
                             style="Dark.TCombobox",
                             font=(FONT_FAMILY, 11))
        combo.grid(row=9, column=0, columnspan=2,
                   padx=24, pady=(4, 20), sticky="ew", ipady=6)

        # ── Action buttons
        btn_frame = tk.Frame(self._right, bg=BG_CARD)
        btn_frame.grid(row=10, column=0, columnspan=2,
                       padx=24, pady=(0, 24), sticky="ew")

        self._btn_save = _make_button(btn_frame, "💾  Save",
                                      self._save_contact,
                                      color=SUCCESS,
                                      hover_color="#16A34A",
                                      width=130, height=40)
        self._btn_save.pack(side="left", padx=(0, 10))

        self._btn_delete = _make_button(btn_frame, "🗑️  Delete",
                                         self._delete_contact,
                                         color=DANGER,
                                         hover_color="#B91C1C",
                                         width=130, height=40)
        self._btn_delete.pack(side="left", padx=(0, 10))

        self._btn_clear = _make_button(btn_frame, "✖  Clear",
                                        self._clear_form,
                                        color=BG_INPUT,
                                        hover_color=BG_HOVER,
                                        width=110, height=40)
        self._btn_clear.pack(side="left")

        # Track name changes to update avatar
        self._vars["name"].trace_add("write", self._update_avatar_preview)

    def _build_field(self, label: str, key: str, icon: str, row: int):
        tk.Label(self._right,
                 text=f"{icon}  {label}",
                 bg=BG_CARD, fg=TEXT_SEC,
                 font=(FONT_FAMILY, 10)).grid(
            row=row, column=0, padx=24, pady=(0, 0), sticky="w")

        entry = tk.Entry(self._right,
                         textvariable=self._vars[key],
                         bg=BG_INPUT, fg=TEXT_PRI,
                         insertbackground=ACCENT,
                         relief="flat", bd=0,
                         font=(FONT_FAMILY, 11),
                         highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
        entry.grid(row=row + 1 - 1 + 1, column=0, columnspan=2,
                   padx=24, pady=(4, 12), sticky="ew", ipady=8)
        # correct row mapping for the entry
        entry.grid(row=row, column=0, columnspan=2,
                   padx=24, pady=(18, 0), sticky="ew", ipady=8)

    # ── Refresh & Search ──────────────────────
    def _refresh_list(self, query: str = ""):
        self._listbox.delete(0, "end")
        if query:
            self._filtered = self.store.search(query)
        else:
            self._filtered = self.store.all()

        for c in self._filtered:
            name  = c.get("name",  "—")
            group = c.get("group", "")
            phone = c.get("phone", "")
            self._listbox.insert("end", f"  {name}   {phone}")

        # Alternate row colours
        for i in range(len(self._filtered)):
            bg = BG_CARD if i % 2 == 0 else BG_INPUT
            self._listbox.itemconfig(i, bg=bg, fg=TEXT_PRI,
                                     selectbackground=ACCENT)

        self._stats_lbl.config(
            text=f"{self.store.count()} contact{'s' if self.store.count() != 1 else ''}")

    def _on_search(self, *_):
        q = self._search_var.get()
        if q == "Search contacts…":
            q = ""
        self._refresh_list(q)

    # ── Event handlers ────────────────────────
    def _on_list_select(self, _):
        sel = self._listbox.curselection()
        if not sel:
            return
        idx   = sel[0]
        contact = self._filtered[idx]
        # Find real index in store
        all_c = self.store.all()
        try:
            self._selected_index = all_c.index(contact)
        except ValueError:
            self._selected_index = None
            return

        self._populate_form(contact)

    def _populate_form(self, c: dict):
        for key, var in self._vars.items():
            var.set(c.get(key, ""))
        self._form_title.config(text="Edit Contact")
        self._form_sub.config(text="Make changes and click Save")
        self._update_avatar(c.get("name", "?"))

    def _update_avatar(self, name: str):
        initials = "".join(w[0].upper() for w in name.split() if w)[:2] or "?"
        self._avatar_canvas.itemconfig(self._avatar_lbl, text=initials)
        self._av_name.config(text=name or "—")
        self._av_group.config(text=self._vars.get("group", tk.StringVar()).get())

    def _update_avatar_preview(self, *_):
        name = self._vars["name"].get()
        self._update_avatar(name)

    # ── CRUD ──────────────────────────────────
    def _new_contact(self):
        self._selected_index = None
        self._clear_form()
        self._form_title.config(text="New Contact")
        self._form_sub.config(text="Fill in the details below and click Save")
        self._update_avatar("?")

    def _validate_form(self) -> bool:
        name  = self._vars["name"].get().strip()
        phone = self._vars["phone"].get().strip()
        email = self._vars["email"].get().strip()

        if not name:
            messagebox.showerror("Validation Error", "Name is required.", parent=self)
            return False
        if not phone:
            messagebox.showerror("Validation Error", "Phone number is required.", parent=self)
            return False
        if not re.match(r"^\+?[\d\s\-\(\)]{7,15}$", phone):
            messagebox.showerror("Validation Error",
                                 "Enter a valid phone number (7-15 digits).",
                                 parent=self)
            return False
        if email and not re.match(r"^[\w\.\+\-]+@[\w\-]+\.\w{2,}$", email):
            messagebox.showerror("Validation Error",
                                 "Enter a valid email address.", parent=self)
            return False
        return True

    def _save_contact(self):
        if not self._validate_form():
            return

        contact = {k: v.get().strip() for k, v in self._vars.items()}

        if self._selected_index is None:
            # Add new
            self.store.add(contact)
            self._show_toast("✅  Contact added successfully!")
        else:
            # Update existing
            self.store.update(self._selected_index, contact)
            self._selected_index = None
            self._show_toast("✅  Contact updated!")

        self._refresh_list()
        self._clear_form()

    def _delete_contact(self):
        if self._selected_index is None:
            messagebox.showinfo("No Selection", "Please select a contact to delete.", parent=self)
            return
        name = self.store.get(self._selected_index).get("name", "this contact")
        confirm = messagebox.askyesno("Delete Contact",
                                      f"Are you sure you want to delete '{name}'?",
                                      parent=self)
        if confirm:
            self.store.delete(self._selected_index)
            self._selected_index = None
            self._refresh_list()
            self._clear_form()
            self._show_toast("🗑️  Contact deleted.")

    def _clear_form(self):
        for var in self._vars.values():
            var.set("")
        self._vars["group"].set("Other")
        self._selected_index = None
        self._form_title.config(text="Select a contact")
        self._form_sub.config(text="or click ＋ New Contact to add one")
        self._update_avatar("?")

    # ── Toast notification ────────────────────
    def _show_toast(self, message: str, duration: int = 2500):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=SUCCESS)

        lbl = tk.Label(toast, text=message,
                       bg=SUCCESS, fg=TEXT_PRI,
                       font=(FONT_FAMILY, 11, "bold"),
                       padx=20, pady=12)
        lbl.pack()

        # Position bottom-centre of main window
        self.update_idletasks()
        wx = self.winfo_x() + self.winfo_width()  // 2
        wy = self.winfo_y() + self.winfo_height() - 80
        tw = 320
        toast.geometry(f"{tw}x44+{wx - tw // 2}+{wy}")

        toast.after(duration, toast.destroy)


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = ContactBookApp()
    app.mainloop()
