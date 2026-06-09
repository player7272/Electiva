import hashlib

from models.database import Database


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class UserModel:
    def __init__(self):
        self.db = Database.get_instance()

    def get_admin_by_credentials(self, correo: str, password: str):
        query = """
            SELECT *
            FROM TUsuarioAdmin
            WHERE cCorreo = %s
              AND cPassword IN (%s, %s)
              AND eEstado = 'Activo'
            LIMIT 1
        """
        row = self.db.fetch_one(query, (correo, _hash(password), password))
        return self._normalize_admin(row) if row else None

    def get_worker_by_credentials(self, identifier: str, password: str):
        query = """
            SELECT t.*, r.cNombre AS cRolNombre
            FROM TTrabajador t
            LEFT JOIN TRoles r ON t.nRolFK = r.nRolID
            WHERE (t.cIdentificacion = %s OR t.cTelefono = %s)
              AND t.cPassword IN (%s, %s)
            LIMIT 1
        """
        row = self.db.fetch_one(
            query,
            (identifier, identifier, _hash(password), password),
        )
        return self._normalize_worker(row) if row else None

    def get_store_for_admin(self, admin_id: int):
        if not self.db.ensure_connected():
            return None

        store = self.db.fetch_one(
            """
            SELECT
                t.nTiendaID AS id,
                COALESCE(t.cNombreComercial, CONCAT('Tienda ', t.nTiendaID)) AS name,
                COALESCE(t.tDescripcion, '') AS description,
                COALESCE(t.cCorreoAtencion, '') AS email,
                COALESCE(t.cTelefonoAtencion, '') AS phone,
                COALESCE(t.cRazonSocial, '') AS legal_name,
                COALESCE(t.cCodigoPostal, '') AS postal_code,
                COALESCE(t.eEstadoTienda, '') AS status,
                '' AS address
            FROM TTiendas t
            WHERE t.nTiendaID = %s
            LIMIT 1
            """,
            (admin_id,),
        )
        if store:
            return self._normalize_store(store)

        store = self.db.fetch_one(
            """
            SELECT
                t.nTiendaID AS id,
                COALESCE(t.cNombreComercial, CONCAT('Tienda ', t.nTiendaID)) AS name,
                COALESCE(t.tDescripcion, '') AS description,
                COALESCE(t.cCorreoAtencion, '') AS email,
                COALESCE(t.cTelefonoAtencion, '') AS phone,
                COALESCE(t.cRazonSocial, '') AS legal_name,
                COALESCE(t.cCodigoPostal, '') AS postal_code,
                COALESCE(t.eEstadoTienda, '') AS status,
                '' AS address
            FROM TTiendas t
            ORDER BY
                CASE WHEN t.eEstadoTienda = 'Activa' THEN 0 ELSE 1 END,
                t.nTiendaID
            LIMIT 1
            """
        )
        return self._normalize_store(store) if store else None

    def get_store_for_worker(self, worker_id: int):
        if not self.db.ensure_connected():
            return None

        store = self.db.fetch_one(
            """
            SELECT
                t.nTiendaID AS id,
                COALESCE(t.cNombreComercial, CONCAT('Tienda ', t.nTiendaID)) AS name,
                COALESCE(t.tDescripcion, '') AS description,
                COALESCE(t.cCorreoAtencion, '') AS email,
                COALESCE(t.cTelefonoAtencion, '') AS phone,
                COALESCE(t.cRazonSocial, '') AS legal_name,
                COALESCE(t.cCodigoPostal, '') AS postal_code,
                COALESCE(t.eEstadoTienda, '') AS status,
                '' AS address
            FROM TTrabajadorTienda tt
            JOIN TTiendas t ON t.nTiendaID = tt.nTiendaFK
            WHERE tt.nTrabajadorFK = %s
            ORDER BY
                CASE WHEN t.eEstadoTienda = 'Activa' THEN 0 ELSE 1 END,
                t.nTiendaID
            LIMIT 1
            """,
            (worker_id,),
        )
        return self._normalize_store(store) if store else self.get_store_for_admin(worker_id)

    @staticmethod
    def _normalize_admin(row):
        name = " ".join(
            part
            for part in (row.get("cNombre"), row.get("cApellido"))
            if part
        ).strip()
        return {
            "id": row.get("nIdUsuario"),
            "name": name or row.get("cCorreo") or "Usuario administrador",
            "email": row.get("cCorreo") or "",
            "role": "admin",
            "role_label": "Administrador",
        }

    @staticmethod
    def _normalize_worker(row):
        name = " ".join(
            part
            for part in (row.get("cNombre"), row.get("cApellido"))
            if part
        ).strip()
        return {
            "id": row.get("nTrabajadorID"),
            "name": name or row.get("cIdentificacion") or "Trabajador",
            "email": row.get("cIdentificacion") or "",
            "role": "worker",
            "role_label": row.get("cRolNombre") or "Trabajador",
            "role_id": row.get("nRolFK"),
        }

    @staticmethod
    def _normalize_store(row):
        return {
            "id": row.get("id"),
            "name": row.get("name") or "Tienda",
            "description": row.get("description") or "",
            "email": row.get("email") or "",
            "phone": row.get("phone") or "",
            "legal_name": row.get("legal_name") or "",
            "postal_code": row.get("postal_code") or "",
            "status": row.get("status") or "",
            "address": row.get("address") or "",
        }

    def get_all_admins(self):
        return self.db.fetch_all("SELECT * FROM TUsuarioAdmin ORDER BY nIdUsuario")

    def get_all_clients(self):
        return self.db.fetch_all(
            "SELECT * FROM TUsuarioCliente ORDER BY nUsuarioClienteID"
        )

    def get_client_by_id(self, client_id: int):
        return self.db.fetch_one(
            """
            SELECT *
            FROM TUsuarioCliente
            WHERE nUsuarioClienteID = %s
            """,
            (client_id,),
        )

    def create_client(self, nombre, apellido, documento, contrasena, correo, telefono):
        query = """
            INSERT INTO TUsuarioCliente
                (cNombre, cApellido, cDocumento, cContrasena, cCorreo, cTelefono)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor = self.db.execute_query(
            query, (nombre, apellido, documento, _hash(contrasena), correo, telefono)
        )
        return cursor is not None

    def update_client(self, client_id, nombre, apellido, documento, correo, telefono):
        query = """
            UPDATE TUsuarioCliente
            SET cNombre=%s, cApellido=%s, cDocumento=%s, cCorreo=%s, cTelefono=%s
            WHERE nUsuarioClienteID=%s
        """
        cursor = self.db.execute_query(
            query, (nombre, apellido, documento, correo, telefono, client_id)
        )
        return cursor is not None

    def delete_client(self, client_id: int):
        cursor = self.db.execute_query(
            "DELETE FROM TUsuarioCliente WHERE nUsuarioClienteID = %s", (client_id,)
        )
        return cursor is not None

    def get_all_workers(self):
        query = """
            SELECT t.*, r.cNombre AS cRolNombre
            FROM TTrabajador t
            LEFT JOIN TRoles r ON t.nRolFK = r.nRolID
            ORDER BY t.nTrabajadorID
        """
        return self.db.fetch_all(query)

    def get_all_roles(self):
        return self.db.fetch_all("SELECT * FROM TRoles ORDER BY nRolID")

    def create_worker(self, identificacion, nombre, apellido, password, telefono, rol_id):
        query = """
            INSERT INTO TTrabajador
                (cIdentificacion, cNombre, cApellido, cPassword, cTelefono, nRolFK)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor = self.db.execute_query(
            query, (identificacion, nombre, apellido, _hash(password), telefono, rol_id)
        )
        return cursor is not None
