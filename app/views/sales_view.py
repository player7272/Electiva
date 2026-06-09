import tkinter as tk
from tkinter import ttk, messagebox


def money(value):
    return f"${float(value or 0):,.0f}".replace(",", ".")


class SalesView(ttk.Frame):
    def __init__(self, parent, controller, on_change=None):
        super().__init__(parent, style="App.TFrame")
        self.controller = controller
        self.on_change = on_change
        self.state_var = tk.StringVar()
        self.state_options = {}
        self.orders = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_actions()
        self._build_body()
        self.refresh()

    def _build_actions(self):
        actions = ttk.LabelFrame(self, text="Gestion de pedidos", padding=14)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        actions.columnconfigure(2, weight=1)

        ttk.Button(actions, text="Refrescar", command=self.refresh).grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Button(
            actions,
            text="Aprobar pedido",
            style="Primary.TButton",
            command=self.approve_order,
        ).grid(row=0, column=1, sticky="w", padx=(0, 18))

        ttk.Label(actions, text="Estado").grid(row=0, column=2, sticky="e", padx=(0, 8))
        self.state_combo = ttk.Combobox(
            actions,
            textvariable=self.state_var,
            state="readonly",
            width=28,
        )
        self.state_combo.grid(row=0, column=3, sticky="ew", padx=(0, 8), ipady=2)
        ttk.Button(
            actions,
            text="Cambiar estado",
            command=self.update_state,
        ).grid(row=0, column=4, sticky="e")

    def _build_body(self):
        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        orders_panel = ttk.LabelFrame(body, text="Pedidos", padding=12)
        orders_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        orders_panel.rowconfigure(0, weight=1)
        orders_panel.columnconfigure(0, weight=1)

        columns = ("id", "date", "customer", "total", "state", "payment")
        self.tree = ttk.Treeview(orders_panel, columns=columns, show="headings", height=15)
        headings = {
            "id": "Pedido",
            "date": "Fecha",
            "customer": "Cliente",
            "total": "Total",
            "state": "Estado",
            "payment": "Pago",
        }
        widths = {
            "id": 75,
            "date": 130,
            "customer": 170,
            "total": 120,
            "state": 145,
            "payment": 160,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")

        scrollbar = ttk.Scrollbar(orders_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail_panel = ttk.LabelFrame(body, text="Pedido y comprobante", padding=12)
        detail_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        detail_panel.rowconfigure(0, weight=1)
        detail_panel.columnconfigure(0, weight=1)

        self.detail_text = tk.Text(
            detail_panel,
            wrap="word",
            height=18,
            bg="#ffffff",
            fg="#182230",
            relief="flat",
            padx=8,
            pady=8,
            font=("Segoe UI", 10),
        )
        self.detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll = ttk.Scrollbar(
            detail_panel,
            orient="vertical",
            command=self.detail_text.yview,
        )
        self.detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.grid(row=0, column=1, sticky="ns")
        self._set_detail("Sin pedido seleccionado.")

    def refresh(self, selected_id=None):
        self._refresh_states()
        self._refresh_orders(selected_id)

    def _refresh_states(self):
        self.state_options = {}
        labels = []
        for state in self.controller.list_states():
            label = f'{state["id"]} - {state["name"]}'
            self.state_options[label] = state["id"]
            labels.append(label)
        self.state_combo.configure(values=labels)
        if labels and self.state_var.get() not in labels:
            self.state_var.set(labels[0])

    def _refresh_orders(self, selected_id=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.orders = {}
        first_id = None
        for order in self.controller.list_orders():
            order_id = str(order["id"])
            self.orders[order_id] = order
            if first_id is None:
                first_id = order_id
            self.tree.insert(
                "",
                "end",
                iid=order_id,
                values=(
                    f'#{order["id"]}',
                    order["created_at"],
                    order["customer"],
                    money(order["total"]),
                    order["state"],
                    self._payment_summary(order),
                ),
            )

        select_id = str(selected_id) if selected_id else first_id
        if select_id and select_id in self.orders:
            self.tree.selection_set(select_id)
            self.tree.focus(select_id)
            self.tree.see(select_id)
            self._show_order(self.orders[select_id])
        else:
            self._set_detail("Sin pedidos para mostrar.")

    def _on_select(self, _event=None):
        order = self._selected_order()
        if order:
            self._show_order(order)

    def _show_order(self, order):
        self._select_state(order.get("state_id"))
        self._set_detail(self._format_order(order))

    def approve_order(self):
        order = self._selected_order()
        if not order:
            messagebox.showwarning("Ventas", "Selecciona un pedido.")
            return

        ok, message = self.controller.approve_order(order["id"])
        if ok:
            self.refresh(order["id"])
            self._notify_change()
            messagebox.showinfo("Ventas", message)
            return
        messagebox.showwarning("Ventas", message)

    def update_state(self):
        order = self._selected_order()
        if not order:
            messagebox.showwarning("Ventas", "Selecciona un pedido.")
            return

        state_id = self.state_options.get(self.state_var.get())
        if not state_id:
            messagebox.showwarning("Ventas", "Selecciona un estado.")
            return

        ok, message = self.controller.update_order_state(order["id"], state_id)
        if ok:
            self.refresh(order["id"])
            self._notify_change()
            messagebox.showinfo("Ventas", message)
            return
        messagebox.showwarning("Ventas", message)

    def _selected_order(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.orders.get(selection[0])

    def _select_state(self, state_id):
        for label, option_id in self.state_options.items():
            if str(option_id) == str(state_id):
                self.state_var.set(label)
                return

    def _payment_summary(self, order):
        status = order.get("payment_status") or "Sin comprobante"
        gateway = order.get("payment_gateway") or ""
        return f"{status} / {gateway}" if gateway else status

    def _format_order(self, order):
        payment_bits = [
            ("Comprobante", order.get("receipt")),
            ("Pasarela", order.get("payment_gateway")),
            ("Referencia", order.get("payment_reference")),
            ("Metodo", order.get("payment_method")),
            ("Franquicia", order.get("payment_brand")),
            ("Ultimos 4", order.get("payment_last4")),
            ("Cuotas", order.get("payment_installments")),
            ("Estado pago", order.get("payment_status")),
            ("Valor pago", money(order.get("payment_amount"))),
            ("Autorizacion", order.get("payment_authorization")),
        ]

        lines = [
            f'Pedido #{order["id"]}',
            f'Tienda: {order.get("store_name") or "Tienda"}',
            f'Cliente: {order.get("customer") or "Cliente mostrador"}',
            f'Fecha: {order.get("created_at") or ""}',
            f'Estado: {order.get("state") or "Sin estado"}',
            "",
            "Pedido del cliente",
            order.get("items") or "Sin detalle",
            "",
            "Valores",
            f'Subtotal: {money(order.get("subtotal"))}',
            f'Envio: {money(order.get("shipping"))}',
            f'Total: {money(order.get("total"))}',
            "",
            "Comprobante de pago",
        ]
        lines.extend(
            f"{label}: {value if value not in (None, '') else 'Sin dato'}"
            for label, value in payment_bits
        )

        raw = order.get("payment_raw")
        if raw:
            lines.extend(("", "Respuesta pasarela", str(raw)))
        return "\n".join(lines)

    def _set_detail(self, text):
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.configure(state="disabled")

    def _notify_change(self):
        if self.on_change:
            self.on_change()
