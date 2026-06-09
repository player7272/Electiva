import json
import os

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql = None
    Error = Exception
else:
    mysql = mysql.connector

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
)

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8080,
    "user": "root",
    "password": "",
    "database": "mercadoshop",
}


class Database:
    _instance = None

    def __init__(self):
        self.connection = None
        self.config = self._load_config()
        self.offline = False
        self.last_error = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        if cls._instance:
            cls._instance.disconnect()
        cls._instance = None

    def _load_config(self):
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
            except Exception:
                pass

        env_map = {
            "host": "DB_HOST",
            "port": "DB_PORT",
            "user": "DB_USER",
            "password": "DB_PASSWORD",
            "database": "DB_NAME",
        }
        for key, env_name in env_map.items():
            value = os.getenv(env_name)
            if value:
                config[key] = int(value) if key == "port" else value
        return self._normalize_config(config)

    def _normalize_config(self, config):
        host = str(config.get("host", "")).strip()
        if ":" in host and host.count(":") == 1:
            host_name, host_port = host.rsplit(":", 1)
            if host_port.isdigit():
                config["host"] = host_name
                config["port"] = int(host_port)

        config["port"] = int(config.get("port", DEFAULT_CONFIG["port"]))
        return config

    def save_config(self, host, port, user, password, database):
        self.config = self._normalize_config(
            {
                "host": host,
                "port": int(port),
                "user": user,
                "password": password,
                "database": database,
            }
        )
        self.offline = False
        self.last_error = None
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")

    def connect(self):
        if self.offline:
            return False
        if mysql is None:
            self.last_error = "mysql-connector-python is not installed."
            self.offline = True
            print(self.last_error)
            return False
        try:
            if self.connection and self.connection.is_connected():
                return True
            self.connection = mysql.connect(
                host=self.config["host"],
                port=self.config.get("port", DEFAULT_CONFIG["port"]),
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                autocommit=False,
                connection_timeout=5,
            )
            self.last_error = None
            return True
        except Error as e:
            self.last_error = str(e)
            print(f"DB Connection Error: {e}")
            self.offline = True
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def ensure_connected(self):
        if not self.connection or not self.connection.is_connected():
            return self.connect()
        return True

    def execute_query(self, query, params=None):
        if not self.ensure_connected():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            self.connection.commit()
            self.last_error = None
            return cursor
        except Error as e:
            self.last_error = str(e)
            print(f"Query Error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return None

    def fetch_all(self, query, params=None):
        if not self.ensure_connected():
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            self.last_error = None
            return cursor.fetchall()
        except Error as e:
            self.last_error = str(e)
            print(f"Fetch Error: {e}")
            return []

    def fetch_one(self, query, params=None):
        if not self.ensure_connected():
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            self.last_error = None
            return cursor.fetchone()
        except Error as e:
            self.last_error = str(e)
            print(f"Fetch Error: {e}")
            return None

    def initialize_schema(self):
        if not self.ensure_connected():
            return False

        statements = [
            """
            CREATE TABLE IF NOT EXISTS TUsuarioAdmin (
                nIdUsuario INT AUTO_INCREMENT PRIMARY KEY,
                cNombre VARCHAR(255),
                cApellido VARCHAR(255),
                cCorreo VARCHAR(255),
                cPassword VARCHAR(255),
                eEstado ENUM('Activo', 'Inactivo', 'Bloqueado') DEFAULT 'Activo',
                dCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TUsuarioCliente (
                nUsuarioClienteID INT AUTO_INCREMENT PRIMARY KEY,
                cNombre VARCHAR(255),
                cApellido VARCHAR(255),
                cDocumento VARCHAR(255),
                cContrasena VARCHAR(255),
                cCorreo VARCHAR(255),
                cTelefono VARCHAR(255),
                nDireccionFK INT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TRoles (
                nRolID INT AUTO_INCREMENT PRIMARY KEY,
                cNombre VARCHAR(255),
                cDescripcion VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TTrabajador (
                nTrabajadorID INT AUTO_INCREMENT PRIMARY KEY,
                cIdentificacion VARCHAR(255),
                cNombre VARCHAR(255),
                cApellido VARCHAR(255),
                cPassword VARCHAR(255),
                cTelefono VARCHAR(255),
                nRolFK INT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TCategoria (
                nCategoriaID INT AUTO_INCREMENT PRIMARY KEY,
                cNombreCategoria VARCHAR(255),
                nCategoriaPadreFK INT,
                bEstado TINYINT(1)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TTiendas (
                nTiendaID INT AUTO_INCREMENT PRIMARY KEY,
                cNombreComercial VARCHAR(255),
                tDescripcion TEXT,
                cUrlLogo VARCHAR(255),
                cCorreoAtencion VARCHAR(255),
                cTelefonoAtencion VARCHAR(255),
                cRazonSocial VARCHAR(255),
                nDireccionFK INT,
                cCodigoPostal VARCHAR(255),
                eEstadoTienda ENUM('Activa', 'Inactiva', 'Suspendida', 'Pendiente'),
                nPlanFK INT,
                dFechaVencimientoSuscripcion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TEstadoPedido (
                nEstadoPedidoID INT AUTO_INCREMENT PRIMARY KEY,
                cNombreEstado VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TProductos (
                nProductoID INT AUTO_INCREMENT PRIMARY KEY,
                nTiendaFK INT,
                cDescripcionCorta VARCHAR(255),
                cDescripcionLarga TEXT,
                cUrlImagenPrincipal VARCHAR(255),
                nCategoriaFK INT,
                jEspecificaciones LONGTEXT,
                nPrecioUnitario DECIMAL(19, 4),
                nCantidadStock INT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TPedido (
                nPedidoID INT AUTO_INCREMENT PRIMARY KEY,
                nClienteFK INT,
                nDireccionClienteFK INT,
                cNumeroComprobante VARCHAR(255),
                nSubtotal DECIMAL(19, 4),
                nCostoEnvio DECIMAL(19, 4),
                nTotal DECIMAL(19, 4),
                nTransaccionPasarelaFK INT,
                nEstadoPedidoFK INT,
                dFechaActualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TDetallePedido (
                nDetallePedidoID INT AUTO_INCREMENT PRIMARY KEY,
                nPedidoFK INT,
                nProductoFK INT,
                cNombreProducto VARCHAR(255),
                nPrecioCompra DECIMAL(19, 4),
                nCantidad INT,
                nSubtotal DECIMAL(19, 4)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TTransaccionPasarela (
                nTransaccionID INT AUTO_INCREMENT PRIMARY KEY,
                nPedidoFK INT,
                cNombrePasarela VARCHAR(255),
                cIdTransaccionExterna VARCHAR(255),
                cMetodoPago VARCHAR(255),
                eFranquicia ENUM('Visa', 'Mastercard', 'AMEX'),
                cUltimos4Digitos VARCHAR(4),
                nCuotas INT,
                nValorTransaccion DECIMAL(19, 4),
                cEstadoTransaccion VARCHAR(255),
                cCodigoAprobacionBanco VARCHAR(255),
                dFechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dFechaActualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                jRawResponse JSON
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS TTrabajadorTienda (
                nID INT AUTO_INCREMENT PRIMARY KEY,
                nTiendaFK INT,
                nTrabajadorFK INT
            )
            """,
        ]

        for statement in statements:
            if self.execute_query(statement) is None:
                return False

        self._seed_roles()
        self._seed_support_tables()
        return True

    def _seed_roles(self):
        roles = (
            ("Administrador", "Acceso administrativo"),
            ("Vendedor", "Registro de ventas"),
            ("Inventario", "Gestion de productos"),
        )
        existing = {
            row["cNombre"]
            for row in self.fetch_all("SELECT cNombre FROM TRoles")
            if row.get("cNombre")
        }
        for role, description in roles:
            if role in existing:
                continue
            self.execute_query(
                "INSERT INTO TRoles (cNombre, cDescripcion) VALUES (%s, %s)",
                (role, description),
            )

    def _seed_support_tables(self):
        if not self.fetch_one("SELECT nCategoriaID FROM TCategoria LIMIT 1"):
            self.execute_query(
                """
                INSERT INTO TCategoria
                    (cNombreCategoria, nCategoriaPadreFK, bEstado)
                VALUES ('General', NULL, 1)
                """
            )

        if not self.fetch_one("SELECT nTiendaID FROM TTiendas LIMIT 1"):
            self.execute_query(
                """
                INSERT INTO TTiendas
                    (cNombreComercial, tDescripcion, eEstadoTienda)
                VALUES ('MercadoShop', 'Tienda principal', 'Activa')
                """
            )

        existing_states = {
            row["cNombreEstado"]
            for row in self.fetch_all("SELECT cNombreEstado FROM TEstadoPedido")
            if row.get("cNombreEstado")
        }
        for state in (
            "Pendiente de Pago",
            "Pago Confirmado",
            "En Preparacion",
            "Enviado",
            "Entregado",
            "Cancelado",
        ):
            if state in existing_states:
                continue
            self.execute_query(
                "INSERT INTO TEstadoPedido (cNombreEstado) VALUES (%s)",
                (state,),
            )
