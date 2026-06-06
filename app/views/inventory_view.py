import tkinter as tk
from tkinter import ttk, messagebox


def money(value):
    return f"${float(value):,.0f}".replace(",", ".")


class InventoryView(ttk.Frame):
    def __init__(self, parent, controller, on_change=None):
        super().__init__(parent, style="App.TFrame")
        self.controller = controller
        self.on_change = on_change
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.delta_var = tk.StringVar(value="1")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_form()
        self._build_table()
        self.refresh()

    def _build_form(self):
        form = ttk.LabelFrame(self, text="Nuevo producto", padding=14)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        for column in range(5):
            form.columnconfigure(column, weight=1)

        self._entry(form, "Nombre", self.name_var, 0)
        self._entry(form, "Categoria", self.category_var, 1)
        self._entry(form, "Precio", self.price_var, 2)
        self._entry(form, "Stock", self.stock_var, 3)
        ttk.Button(
            form,
            text="Crear producto",
            style="Primary.TButton",
            command=self.create_product,
        ).grid(row=1, column=4, sticky="ew", padx=(10, 0))

    def _entry(self, parent, label, variable, column):
        ttk.Label(parent, text=label).grid(row=0, column=column, sticky="w", padx=(0, 8))
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=1, column=column, sticky="ew", padx=(0, 8), ipady=3)
        return entry

    def _build_table(self):
        panel = ttk.LabelFrame(self, text="Catalogo", padding=12)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        columns = ("id", "name", "category", "price", "stock", "status")
        self.tree = ttk.Treeview(panel, columns=columns, show="headings", height=15)
        headings = {
            "id": "ID",
            "name": "Producto",
            "category": "Categoria",
            "price": "Precio",
            "stock": "Stock",
            "status": "Estado",
        }
        widths = {
            "id": 55,
            "name": 250,
            "category": 140,
            "price": 110,
            "stock": 90,
            "status": 100,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        actions = ttk.Frame(panel, style="Surface.TFrame")
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(actions, text="Ajuste de stock").pack(side="left")
        ttk.Entry(actions, textvariable=self.delta_var, width=8).pack(
            side="left", padx=(8, 6)
        )
        ttk.Button(actions, text="Aplicar", command=self.adjust_stock).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(actions, text="+1", command=lambda: self.adjust_stock(1)).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(actions, text="-1", command=lambda: self.adjust_stock(-1)).pack(
            side="left"
        )

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for product in self.controller.list_products():
            self.tree.insert(
                "",
                "end",
                iid=str(product["id"]),
                values=(
                    product["id"],
                    product["name"],
                    product["category"],
                    money(product["price"]),
                    product["stock"],
                    product["status"],
                ),
            )

    def create_product(self):
        ok, message = self.controller.create_product(
            self.name_var.get(),
            self.category_var.get(),
            self.price_var.get(),
            self.stock_var.get(),
        )
        if ok:
            self.name_var.set("")
            self.category_var.set("")
            self.price_var.set("")
            self.stock_var.set("")
            self.refresh()
            self._notify_change()
            messagebox.showinfo("Inventario", message)
            return
        messagebox.showwarning("Inventario", message)

    def adjust_stock(self, fixed_delta=None):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Inventario", "Selecciona un producto.")
            return

        delta = fixed_delta if fixed_delta is not None else self.delta_var.get()
        ok, message = self.controller.adjust_stock(selection[0], delta)
        if ok:
            self.refresh()
            self._notify_change()
            messagebox.showinfo("Inventario", message)
            return
        messagebox.showwarning("Inventario", message)

    def _notify_change(self):
        if self.on_change:
            self.on_change()
