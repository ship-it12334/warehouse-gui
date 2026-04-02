import requests
import json
from datetime import date, timedelta
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ===== CONFIG =====
TOKEN = "461818415"
HUB_ID = 1
MOBILE_SECRET = "473821fjisak8592"

BASE_URL = "https://api.nextlevel.delivery"
DELAY = 1.0
# ==================

session = requests.Session()
current_user_key = None

# Color palette
COLORS = {
    "bg": "#f7f9fc",
    "card_bg": "#ffffff",
    "header_start": "#4f46e5",
    "header_end": "#06b6d4",
    "text": "#1f2937",
    "muted": "#6b7280",
    "accent_green": "#10b981",
    "accent_blue": "#3b82f6",
    "accent_orange": "#f59e0b",
    "accent_red": "#ef4444",
    "accent_purple": "#8b5cf6",
    "border": "#e5e7eb",
    "tree_header": "#111827",
    "tree_alt": "#f9fafb",
}

def get_auth_key():
    global current_user_key
    login_url = f"{BASE_URL}/admin/login/qr"
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://admin.nextlevel.delivery",
        "x-mobile-secret": MOBILE_SECRET,
    }
    data = {"token": TOKEN}

    try:
        resp = session.post(login_url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()

        if result.get("success"):
            current_user_key = result["key"]
            session.headers["x-user-key"] = current_user_key
            return True, None
        return False, "Login response success=false"
    except Exception as e:
        return False, str(e)

def _get(path, params=None):
    url = f"{BASE_URL}{path}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_all_stats():
    to = date.today()
    from_ = to - timedelta(days=30)
    from_str = from_.isoformat()
    to_str = to.isoformat()

    stats = _get("/admin/fulfillment-stats/recent")
    time.sleep(DELAY)
    revenue = _get("/admin/fulfillment-invoices/revenue-by-month")
    time.sleep(DELAY)
    recent = _get("/admin/stats/recent", params={"from": from_str, "to": to_str})
    time.sleep(DELAY)
    financial = _get("/admin/stats/financial-summary", params={"from": from_str, "to": to_str})

    return {
        "from": from_str,
        "to": to_str,
        "fulfillment_stats": stats,
        "revenue_by_month": revenue,
        "recent_stats": recent,
        "financial_summary": financial,
    }

def format_number(val):
    if isinstance(val, (int, float)):
        return f"{val:,.2f}"
    s = str(val).replace(" ", "").replace(",", "")
    try:
        f = float(s)
        return f"{f:,.2f}"
    except ValueError:
        return str(val)

def choose_color_for_value(key, value):
    # Simple heuristic for card accent color
    k = key.lower()
    if "progress" in k:
        try:
            v = int(str(value).replace("-", ""))
            if value is None:
                return COLORS["accent_blue"]
            if str(value).startswith("-"):
                return COLORS["accent_red"]
            return COLORS["accent_green"]
        except ValueError:
            return COLORS["accent_blue"]
    if any(x in k for x in ["today", "this_week", "this_month", "created", "pickup"]):
        return COLORS["accent_blue"]
    if any(x in k for x in ["not_picked", "not_collected"]):
        return COLORS["accent_orange"]
    if any(x in k for x in ["cod", "payment", "paid"]):
        return COLORS["accent_green"]
    if any(x in k for x in ["weight", "price", "total"]):
        return COLORS["accent_purple"]
    return COLORS["accent_blue"]

def build_gui():
    root = tk.Tk()
    root.title("NextLevel Delivery – Stats Dashboard")
    root.geometry("1200x800")
    root.configure(bg=COLORS["bg"])

    # Fonts
    font_title = ("Segoe UI", 16, "bold")
    font_heading = ("Segoe UI", 12, "bold")
    font_normal = ("Segoe UI", 10)
    font_big = ("Segoe UI", 11, "bold")

    main_frame = tk.Frame(root, bg=COLORS["bg"])
    main_frame.pack(fill="both", expand=True, padx=12, pady=12)

    # Header
    header = tk.Frame(main_frame, bg=COLORS["header_start"], height=70)
    header.pack(fill="x", pady=(0, 12))
    header.pack_propagate(False)

    header_title = tk.Label(
        header,
        text="NextLevel Delivery – Stats Dashboard",
        font=font_title,
        fg="#ffffff",
        bg=COLORS["header_start"],
        anchor="w",
        padx=15,
        pady=15,
    )
    header_title.pack(side="left", fill="x", expand=True)

    status_var = tk.StringVar(value="Ready")
    status_label = tk.Label(
        header,
        textvariable=status_var,
        font=font_normal,
        fg="#e5e7eb",
        bg=COLORS["header_start"],
        padx=15,
        pady=15,
    )
    status_label.pack(side="right")

    # Notebook (tabs)
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.TNotebook",
        background=COLORS["bg"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["bg"],
        darkcolor=COLORS["bg"],
    )
    style.configure(
        "Custom.TNotebook.Tab",
        padding=[15, 8],
        font=("Segoe UI", 11),
        background=COLORS["card_bg"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["card_bg"],
        darkcolor=COLORS["card_bg"],
    )
    style.map(
        "Custom.TNotebook.Tab",
        background=[("selected", COLORS["header_start"])],
        foreground=[("selected", "#ffffff")],
    )

    notebook = ttk.Notebook(main_frame, style="Custom.TNotebook")
    notebook.pack(fill="both", expand=True)

    tab_fulfillment = tk.Frame(notebook, bg=COLORS["bg"])
    tab_revenue = tk.Frame(notebook, bg=COLORS["bg"])
    tab_recent = tk.Frame(notebook, bg=COLORS["bg"])
    tab_financial = tk.Frame(notebook, bg=COLORS["bg"])

    notebook.add(tab_fulfillment, text="Fulfillment Stats")
    notebook.add(tab_revenue, text="Revenue by Month")
    notebook.add(tab_recent, text="Recent Stats")
    notebook.add(tab_financial, text="Financial Summary")

    # Card creator
    def make_card(parent, title, text, row, col, accent_color=None):
        card = tk.Frame(parent, bg=COLORS["card_bg"], highlightbackground=accent_color or COLORS["accent_blue"], highlightthickness=2, relief="flat")
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        parent.columnconfigure(col, weight=1)

        tk.Label(
            card,
            text=title,
            font=font_heading,
            fg=COLORS["muted"],
            bg=COLORS["card_bg"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        tk.Label(
            card,
            text=str(text),
            font=font_big,
            fg=accent_color or COLORS["text"],
            bg=COLORS["card_bg"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 10))

        return card

    # ---------- Fulfillment Stats Tab ----------
    def fill_fulfillment(data):
        for w in tab_fulfillment.winfo_children():
            w.destroy()

        stats = data["fulfillment_stats"]

        tk.Label(
            tab_fulfillment,
            text="Fulfillment Overview",
            font=font_title,
            fg=COLORS["text"],
            bg=COLORS["bg"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        fields = [
            ("Fulfilled Today", stats.get("fulfilled_today")),
            ("Fulfilled Yesterday", stats.get("fulfilled_yesterday")),
            ("Fulfilled This Week", stats.get("fulfilled_this_week")),
            ("Fulfilled Last 7 Days", stats.get("fulfilled_last_7_days")),
            ("Fulfilled This Month", stats.get("fulfilled_this_month")),
            ("Fulfilled Last 30 Days", stats.get("fulfilled_last_30_days")),
            ("Today Progress", stats.get("fulfilled_today_progress")),
            ("This Week Progress", stats.get("fulfilled_this_week_progress")),
            ("This Month Progress", stats.get("fulfilled_this_month_progress")),
        ]

        for i, (title, val) in enumerate(fields):
            row = 1 + i // 3
            col = i % 3
            accent = choose_color_for_value(title, val)
            make_card(tab_fulfillment, title, str(val), row, col, accent)

    # ---------- Revenue by Month Tab ----------
    def fill_revenue(data):
        for w in tab_revenue.winfo_children():
            w.destroy()

        tk.Label(
            tab_revenue,
            text="Revenue by Month (EUR)",
            font=font_title,
            fg=COLORS["text"],
            bg=COLORS["bg"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Treeview style
        tree_style = ttk.Style()
        tree_style.configure(
            "Custom.Treeview",
            background=COLORS["card_bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["card_bg"],
            rowheight=28,
            font=font_normal,
        )
        tree_style.configure(
            "Custom.Treeview.Heading",
            background=COLORS["header_start"],
            foreground="#ffffff",
            font=("Segoe UI", 11, "bold"),
        )

        cols = ("Month", "Amount EUR")
        tree = ttk.Treeview(tab_revenue, columns=cols, show="headings", style="Custom.Treeview")
        tree.heading("Month", text="Month")
        tree.heading("Amount EUR", text="Amount (EUR)")
        tree.column("Month", width=180, anchor="w")
        tree.column("Amount EUR", width=180, anchor="e")

        # Alternate row colors via tags
        tree.tag_configure("oddrow", background=COLORS["tree_alt"])
        tree.tag_configure("evenrow", background=COLORS["card_bg"])

        scrollbar = ttk.Scrollbar(tab_revenue, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        tab_revenue.columnconfigure(0, weight=1)
        tab_revenue.rowconfigure(1, weight=1)

        months = data["revenue_by_month"].get("months", [])
        for idx, m in enumerate(months):
            label = m.get("label", "")
            amount = m.get("amount_eur", 0)
            tag = "oddrow" if idx % 2 else "evenrow"
            tree.insert("", "end", values=(label, f"{amount:,.2f}"), tags=(tag,))

    # ---------- Recent Stats Tab ----------
    def fill_recent(data):
        for w in tab_recent.winfo_children():
            w.destroy()

        stats = data["recent_stats"]
        from_str = data["from"]
        to_str = data["to"]

        tk.Label(
            tab_recent,
            text=f"Recent Stats ({from_str} → {to_str})",
            font=font_title,
            fg=COLORS["text"],
            bg=COLORS["bg"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        fields = [
            ("Created Today", stats.get("created_today")),
            ("Not Picked Up", stats.get("not_pickedup")),
            ("Not Picked Up (7d)", stats.get("not_pickedup_7")),
            ("Not Picked Up (30d)", stats.get("not_pickedup_30")),
            ("Pickup Today", stats.get("pickup_today")),
            ("Pickup This Week", stats.get("pickup_this_week")),
            ("Pickup This Month", stats.get("pickup_this_month")),
            ("Today Progress", stats.get("pickup_today_progress")),
            ("This Week Progress", stats.get("pickup_this_week_progress")),
            ("This Month Progress", stats.get("pickup_this_month_progress")),
            ("Last Month Workdays", stats.get("last_month_workdays")),
            ("This Month Workdays", stats.get("this_month_workdays")),
            ("Last Month Avg", stats.get("last_month_average")),
            ("This Month Avg", stats.get("this_month_average")),
            ("This Month Expected", stats.get("this_month_expected")),
            ("Expected Progress", stats.get("this_month_expected_progress")),
        ]

        for i, (title, val) in enumerate(fields):
            row = 1 + i // 4
            col = i % 4
            accent = choose_color_for_value(title, val)
            make_card(tab_recent, title, str(val), row, col, accent)

    # ---------- Financial Summary Tab ----------
    def fill_financial(data):
        for w in tab_financial.winfo_children():
            w.destroy()

        stats = data["financial_summary"]
        from_str = data["from"]
        to_str = data["to"]

        tk.Label(
            tab_financial,
            text=f"Financial Summary ({from_str} → {to_str})",
            font=font_title,
            fg=COLORS["text"],
            bg=COLORS["bg"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        weight_fields = [
            ("Min Weight (kg)", stats.get("min_weight")),
            ("Max Weight (kg)", stats.get("max_weight")),
            ("Avg Weight (kg)", stats.get("avg_weight")),
        ]
        cod_fields = [
            ("Min COD", stats.get("min_cod")),
            ("Max COD", stats.get("max_cod")),
            ("Avg COD", stats.get("avg_cod")),
            ("Total COD", stats.get("cod")),
            ("In Delivery COD", stats.get("in_delivery_cod")),
            ("Not Collected COD", stats.get("not_collected_cod")),
            ("Prepaid to Customer COD", stats.get("prepaid_to_customer_cod")),
            ("For Payment", stats.get("for_payment")),
            ("Paid to Customer", stats.get("paid_to_customer")),
        ]
        price_fields = [
            ("Min Base Price", stats.get("min_base_price")),
            ("Max Base Price", stats.get("max_base_price")),
            ("Avg Base Price", stats.get("avg_base_price")),
            ("Min Total Price", stats.get("min_total_price")),
            ("Max Total Price", stats.get("max_total_price")),
            ("Avg Total Price", stats.get("avg_total_price")),
        ]
        totals_fields = [
            ("Total Price", stats.get("total_price")),
            ("Total Base Price", stats.get("total_base_price")),
            ("Total Taxes", stats.get("total_taxes_price")),
            ("Total Services", stats.get("total_services_price")),
        ]

        all_fields = weight_fields + cod_fields + price_fields + totals_fields

        for i, (title, val) in enumerate(all_fields):
            r = 1 + i // 2
            c = (i % 2) * 2
            accent = choose_color_for_value(title, val)
            # Title
            tk.Label(
                tab_financial,
                text=title,
                font=font_normal,
                fg=COLORS["muted"],
                bg=COLORS["bg"],
                anchor="w",
            ).grid(row=r, column=c, sticky="w", padx=12, pady=4)
            # Value
            tk.Label(
                tab_financial,
                text=format_number(val) if val is not None else "",
                font=font_big,
                fg=accent,
                bg=COLORS["bg"],
                anchor="w",
            ).grid(row=r, column=c+1, sticky="w", padx=12, pady=4)

        for col in range(4):
            tab_financial.columnconfigure(col, weight=1)

    data_holder = {}

    def on_load():
        status_var.set("Logging in...")
        root.update()
        ok, err = get_auth_key()
        if not ok:
            messagebox.showerror("Login failed", f"Could not log in:\n{err}")
            status_var.set("Ready (login failed)")
            return

        status_var.set("Fetching stats...")
        root.update()
        try:
            data = fetch_all_stats()
            data_holder["data"] = data
            fill_fulfillment(data)
            fill_revenue(data)
            fill_recent(data)
            fill_financial(data)
            status_var.set("Ready (data loaded)")
        except Exception as e:
            messagebox.showerror("Fetch error", f"Could not fetch stats:\n{e}")
            status_var.set("Ready (fetch failed)")

    # Toolbar
    toolbar = tk.Frame(main_frame, bg=COLORS["bg"])
    toolbar.pack(fill="x", pady=(12, 0))

    btn_load = tk.Button(
        toolbar,
        text="⟳ Refresh Stats",
        command=on_load,
        font=("Segoe UI", 10, "bold"),
        bg=COLORS["header_start"],
        fg="#ffffff",
        activebackground=COLORS["header_end"],
        activeforeground="#ffffff",
        relief="flat",
        padx=16,
        pady=6,
        border=0,
    )
    btn_load.pack(side="left")

    tk.Label(
        toolbar,
        text="Tip: Close and reopen to refresh, or use the button.",
        font=font_normal,
        fg=COLORS["muted"],
        bg=COLORS["bg"],
    ).pack(side="left", padx=12)

    # Initial load
    on_load()

    root.mainloop()

if __name__ == "__main__":
    build_gui()