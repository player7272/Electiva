from models.user_model import UserModel
from api_client import get_api_client


class AuthController:
    def __init__(self):
        self.users = UserModel()
        self.current_user = None
        self.current_store = None
        self._api = get_api_client()

    @property
    def is_authenticated(self):
        return self.current_user is not None

    def login(self, email, password):
        email = (email or "").strip()
        password = password or ""
        if not email or not password:
            return False, "Credenciales incompletas."

        # Intentar login via API para administradores si el identificador parece un correo
        try:
            if self._api and "@" in email:
                # admin login
                payload = {"cCorreo": email, "cPassword": password}
                resp = self._api.post("/api/auth/admin/login", payload)
                token = resp.get("token")
                admin = resp.get("admin")
                if token and admin:
                    self._api.set_token(token)
                    self.current_user = {
                        "id": admin.get("nIdUsuario"),
                        "name": f"{admin.get('cNombre','')} {admin.get('cApellido','')}".strip(),
                        "email": admin.get("cCorreo"),
                        "role": "admin",
                        "role_label": "Administrador",
                        "role_id": 4,
                    }
                    # intentar obtener tiendas con token (tomar la primera disponible)
                    tiendas = self._api.get_admin_tiendas() or []
                    self.current_store = tiendas[0] if tiendas else None
                    store_name = self.current_store.get("cNombreComercial") if self.current_store else "sin tienda"
                    return True, f"Sesion iniciada para Administrador. Tienda: {store_name}."

        except Exception:
            # Ignorar y seguir con el flujo local
            pass

        # Intento de login local (workers o fallback)
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
                self.current_user["role_id"] = 4

            # Si tenemos API y es trabajador, intentar obtener token via API worker login
            try:
                if self._api and user.get("role") == "worker" and self.current_store:
                    payload = {
                        "cIdentificacion": user.get("email") or user.get("id"),
                        "cPassword": password,
                        "nTiendaFK": self.current_store.get("id")
                    }
                    resp = self._api.post("/api/auth/trabajador/login", payload)
                    token = resp.get("token")
                    if token:
                        self._api.set_token(token)
            except Exception:
                pass

            store_name = self.current_store["name"] if self.current_store else "sin tienda"
            role_label = user.get("role_label", "Usuario")
            return True, f"Sesion iniciada para {role_label}. Tienda: {store_name}."

        return False, "Credenciales invalidas."

    def logout(self):
        self.current_user = None
        self.current_store = None
        self._api.set_token(None)

    @property
    def allowed_sections(self):
        if not self.current_user:
            return set()

        if self.current_user.get("role") == "admin":
            return {"dashboard", "inventory", "sales"}

        role_id = int(self.current_user.get("role_id") or 0)
        if role_id in (1, 4):
            return {"dashboard", "inventory", "sales"}
        if role_id in (2, 5):
            return {"sales"}
        if role_id in (3, 6):
            return {"inventory"}
        return set()

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
