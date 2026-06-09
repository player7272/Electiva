import tkinter as tk
from tkinter import ttk, messagebox


class LoginView(ttk.Frame):
    def __init__(self, parent, controller, on_success=None):
        super().__init__(parent, style="App.TFrame")
        self.controller = controller
        self.on_success = on_success
        self.email_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")

        self._build()

    def _build(self):
        panel = ttk.LabelFrame(self, text="Ingreso de personal", padding=18)
        panel.grid(row=0, column=0, sticky="nw")

        ttk.Label(panel, text="Correo, identificacion o telefono").grid(row=0, column=0, sticky="w")
        email_entry = ttk.Entry(panel, textvariable=self.email_var, width=36)
        email_entry.grid(row=1, column=0, sticky="ew", pady=(4, 12), ipady=3)

        ttk.Label(panel, text="Contrasena").grid(row=2, column=0, sticky="w")
        password_entry = ttk.Entry(
            panel,
            textvariable=self.password_var,
            show="*",
            width=36,
        )
        password_entry.grid(row=3, column=0, sticky="ew", pady=(4, 14), ipady=3)

        ttk.Button(
            panel,
            text="Ingresar",
            style="Primary.TButton",
            command=self.submit,
        ).grid(row=4, column=0, sticky="ew")

        email_entry.focus_set()
        password_entry.bind("<Return>", lambda _event: self.submit())

    def submit(self):
        ok, message = self.controller.login(
            self.email_var.get(),
            self.password_var.get(),
        )
        if ok:
            if self.on_success:
                self.on_success(message)
            return
        messagebox.showwarning("MercadoShop", message)
