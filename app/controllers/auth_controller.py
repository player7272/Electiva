from models.user_model import UserModel


class AuthController:
    def __init__(self):
        self.users = UserModel()
        self.current_user = None
        self.current_store = None

    @property
    def is_authenticated(self):
        return self.current_user is not None

    def login(self, email, password):
        email = (email or "").strip()
        password = password or ""
        if not self.users.db.ensure_connected():
            return False, "No se puede cargar la base de datos."

        user = self.users.get_admin_by_credentials(email, password)
        if not user:
            user = self.users.get_worker_by_credentials(email, password)

        if user:
            self.current_user = user
            if user.get("role") == "worker":
                self.current_store = self.users.get_store_for_worker(user["id"])
            else:
                self.current_store = self.users.get_store_for_admin(user["id"])
            store_name = self.current_store["name"] if self.current_store else "sin tienda"
            role_label = user.get("role_label", "Usuario")
            return True, f"Sesion iniciada para {role_label}. Tienda: {store_name}."

        return False, "Credenciales invalidas."

    def logout(self):
        self.current_user = None
        self.current_store = None

    def user_label(self):
        if not self.current_user:
            return "Sin sesion"
        email = self.current_user.get("email")
        role = self.current_user.get("role_label")
        label = self.current_user["name"]
        if role:
            label = f"{label} ({role})"
        if email:
            label = f"{label} <{email}>"
        return label

    def store_label(self):
        if not self.current_store:
            return ""
        return self.current_store["name"]
