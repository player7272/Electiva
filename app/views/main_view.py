import tkinter as tk
from tkinter import ttk, messagebox

from controllers.auth_controller import AuthController
from controllers.inventory_controller import InventoryController
from controllers.sales_controller import SalesController
from models.database import Database
from views.inventory_view import InventoryView
from views.login_view import LoginView
from views.sales_view import SalesView


def money(value):
    return f"${float(value):,.0f}".replace(",", ".")


class MainView:
    def __init__(self, root):
        self.root = root
        self.auth_controller = AuthController()
        self.inventory_controller = InventoryController()
        self.sales_controller = SalesController()
        self.current_view = None
        self.nav_buttons = {}
        self.title_var = tk.StringVar(value="Resumen operativo")
        self.user_var = tk.StringVar(value="Sin sesion")
        self.db_var = tk.StringVar(value=self._database_status())

        self._configure_styles()
        self._build_shell()
        self.show_login()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Surface.TFrame", background="#ffffff")
        style.configure("Header.TLabel", background="#ffffff", foreground="#182230")
        style.configure(
            "Title.TLabel",
            background="#ffffff",
            foreground="#182230",
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Muted.TLabel",
            background="#ffffff",
            foreground="#667085",
            font=("Segoe UI", 10),
        )
        style.configure("Panel.TLabelframe", background="#ffffff")
        style.configure(
            "Panel.TLabelframe.Label",
            background="#ffffff",
            foreground="#182230",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Treeview",
            rowheight=30,
            font=("Segoe UI", 10),
            fieldbackground="#ffffff",
            background="#ffffff",
            foreground="#182230",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            foreground="#475467",
        )
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _build_shell(self):
        shell = ttk.Frame(self.root, style="App.TFrame")
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(shell, bg="#111827", width=220)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        brand = tk.Label(
            self.sidebar,
            text="MercadoShop\nEscritorio",
            bg="#111827",
            fg="#f9fafb",
            justify="left",
            font=("Segoe UI", 17, "bold"),
            padx=18,
            pady=22,
        )
        brand.pack(anchor="w")

        self._nav_button("Resumen", "dashboard", self.show_dashboard)
        self._nav_button("Inventario", "inventory", self.show_inventory)
        self._nav_button("Ventas", "sales", self.show_sales)
        self._nav_button("Ingreso", "login", self.show_login)

        tk.Label(
            self.sidebar,
            textvariable=self.db_var,
            bg="#111827",
            fg="#cbd5e1",
            justify="left",
            wraplength=175,
            padx=18,
            pady=18,
            font=("Segoe UI", 9),
        ).pack(side="bottom", anchor="w")

        main = ttk.Frame(shell, style="App.TFrame")
        main.grid(row=0, column=1, sticky="nsew")
        main.rowconfigure(1, weight=1)
        main.columnconfigure(0, weight=1)

        header = ttk.Frame(main, style="Surface.TFrame", padding=(24, 16))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, textvariable=self.title_var, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, textvariable=self.user_var, style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )
        self.logout_button = ttk.Button(header, text="Cerrar sesion", command=self.logout)
        self.logout_button.grid(
            row=0, column=1, rowspan=2, sticky="e"
        )

        self.content = ttk.Frame(main, style="App.TFrame", padding=24)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

    def _nav_button(self, text, key, command):
        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            anchor="w",
            relief="flat",
            bd=0,
            bg="#111827",
            fg="#cbd5e1",
            activebackground="#263244",
            activeforeground="#ffffff",
            padx=18,
            pady=12,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            disabledforeground="#64748b",
        )
        button.pack(fill="x", padx=10, pady=2)
        self.nav_buttons[key] = button

    def _set_active(self, key):
        for button_key, button in self.nav_buttons.items():
            if button_key == key:
                button.configure(bg="#263244", fg="#ffffff")
            else:
                button.configure(bg="#111827", fg="#cbd5e1")

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.current_view = None

    def _database_status(self):
        db = Database.get_instance()
        if db.ensure_connected():
            if db.last_error:
                return "No se puede cargar la base de datos"
            return f"Base de datos: MySQL en {db.config['host']}:{db.config['port']}"
        return "No se puede cargar la base de datos"

    def _refresh_status(self):
        if self.auth_controller.is_authenticated:
            label = self.auth_controller.user_label()
            store = self.auth_controller.store_label()
            if store:
                label = f"{label} | {store}"
            self.user_var.set(label)
        else:
            self.user_var.set("Sin sesion")
        self.db_var.set(self._database_status())
        self._sync_session_controls()

    def _sync_session_controls(self):
        allowed = self.auth_controller.allowed_sections
        for key in ("dashboard", "inventory", "sales"):
            self.nav_buttons[key].configure(state="normal" if key in allowed else "disabled")
        self.nav_buttons["login"].configure(state="disabled" if self.auth_controller.is_authenticated else "normal")
        self.logout_button.configure(state="normal" if self.auth_controller.is_authenticated else "disabled")

    def _require_session(self):
        if self.auth_controller.is_authenticated:
            return True
        self.show_login()
        return False

    def _apply_session_context(self):
        store = self.auth_controller.current_store or {}
        store_id = store.get("id")
        self.inventory_controller.set_store_id(store_id)
        self.sales_controller.set_store_id(store_id)

    def show_dashboard(self):
        if not self._require_session():
            return
        if "dashboard" not in self.auth_controller.allowed_sections:
            messagebox.showwarning("MercadoShop", "No tienes permiso para acceder al panel.")
            return
        self._set_active("dashboard")
        self._clear_content()
        self.title_var.set("Resumen operativo")
        self._refresh_status()

        frame = ttk.Frame(self.content, style="App.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        summary = self.inventory_controller.summary()
        low_stock = self.inventory_controller.low_stock()
        sales = self.sales_controller.recent_sales()[:6]
        store = self.auth_controller.current_store or {}

        metrics = ttk.Frame(frame, style="App.TFrame")
        metrics.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        for column in range(4):
            metrics.columnconfigure(column, weight=1)

        self._metric(metrics, "Productos", summary["total_products"], 0)
        self._metric(metrics, "Unidades", summary["total_units"], 1)
        self._metric(metrics, "Valor inventario", money(summary["inventory_value"]), 2)
        self._metric(metrics, "Stock bajo", summary["low_stock"], 3)

        store_panel = ttk.LabelFrame(
            frame, text="Tienda administrada", style="Panel.TLabelframe", padding=12
        )
        store_panel.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 18))
        self._store_summary(store_panel, store)

        low_panel = ttk.LabelFrame(
            frame, text="Stock bajo", style="Panel.TLabelframe", padding=12
        )
        low_panel.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
        self._dashboard_tree(
            low_panel,
            ("Producto", "Categoria", "Stock"),
            [
                (product["name"], product["category"], f'{product["stock"]} uds')
                for product in low_stock
            ],
        )

        sales_panel = ttk.LabelFrame(
            frame, text="Ventas recientes", style="Panel.TLabelframe", padding=12
        )
        sales_panel.grid(row=2, column=1, sticky="nsew", padx=(8, 0))
        self._dashboard_tree(
            sales_panel,
            ("Cliente", "Detalle", "Total"),
            [(sale["customer"], sale["items"], money(sale["total"])) for sale in sales],
        )

    def _store_summary(self, parent, store):
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        fields = (
            ("Nombre", store.get("name", "Sin tienda")),
            ("Estado", store.get("status", "")),
            ("Correo", store.get("email", "")),
            ("Telefono", store.get("phone", "")),
            ("Razon social", store.get("legal_name", "")),
            ("Descripcion", store.get("description", "")),
        )
        for index, (label, value) in enumerate(fields):
            row = index // 2
            column = index % 2
            text = f"{label}: {value or 'Sin dato'}"
            ttk.Label(parent, text=text, style="Header.TLabel", wraplength=420).grid(
                row=row, column=column, sticky="w", padx=(0, 18), pady=3
            )

    def _metric(self, parent, label, value, column):
        card = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#d9e2ec")
        card.grid(row=0, column=column, sticky="ew", padx=6)
        tk.Label(
            card,
            text=label.upper(),
            bg="#ffffff",
            fg="#667085",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(
            card,
            text=str(value),
            bg="#ffffff",
            fg="#182230",
            font=("Segoe UI", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 14))

    def _dashboard_tree(self, parent, columns, rows):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=9)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=150, anchor="w")
        tree.pack(fill="both", expand=True)
        if rows:
            for row in rows:
                tree.insert("", "end", values=row)
        else:
            tree.insert("", "end", values=("Sin datos", "", ""))

    def show_inventory(self):
        if not self._require_session():
            return
        if "inventory" not in self.auth_controller.allowed_sections:
            messagebox.showwarning("MercadoShop", "No tienes permiso para acceder a inventario.")
            return
        self._set_active("inventory")
        self._clear_content()
        self.title_var.set("Inventario")
        self._refresh_status()
        self.current_view = InventoryView(
            self.content,
            self.inventory_controller,
            on_change=self._refresh_status,
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_sales(self):
        if not self._require_session():
            return
        if "sales" not in self.auth_controller.allowed_sections:
            messagebox.showwarning("MercadoShop", "No tienes permiso para acceder a ventas.")
            return
        self._set_active("sales")
        self._clear_content()
        self.title_var.set("Ventas")
        self._refresh_status()
        self.current_view = SalesView(
            self.content,
            self.sales_controller,
            on_change=self._refresh_status,
        )
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def show_login(self):
        self._set_active("login")
        self._clear_content()
        self.title_var.set("Ingreso de personal")
        self._refresh_status()
        self.current_view = LoginView(
            self.content,
            self.auth_controller,
            on_success=self._login_success,
        )
        self.current_view.grid(row=0, column=0, sticky="nw")

    def _login_success(self, message):
        self._apply_session_context()
        self._refresh_status()
        messagebox.showinfo("MercadoShop", message)
        allowed = self.auth_controller.allowed_sections
        if "dashboard" in allowed:
            self.show_dashboard()
        elif "sales" in allowed:
            self.show_sales()
        elif "inventory" in allowed:
            self.show_inventory()
        else:
            messagebox.showwarning("MercadoShop", "No tienes acceso asignado a ninguna sección.")
            self.show_login()

    def logout(self):
        if not self.auth_controller.current_user:
            messagebox.showinfo("MercadoShop", "No hay una sesion activa.")
            self.show_login()
            return
        self.auth_controller.logout()
        self._apply_session_context()
        self._refresh_status()
        messagebox.showinfo("MercadoShop", "Sesion cerrada.")
        self.show_login()
