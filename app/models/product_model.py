from decimal import Decimal
import os

from models.database import Database
from api_client import get_api_client

_USE_API = str(os.getenv("USE_API", "0")).lower() in ("1", "true", "yes")
_API = get_api_client() if _USE_API else None


SEED_PRODUCTS = [
    {
        "name": "Arroz Diana 500g",
        "category": "Granos",
        "price": 2800,
        "stock": 42,
        "status": "Activo",
    },
    {
        "name": "Aceite vegetal 900ml",
        "category": "Despensa",
        "price": 9700,
        "stock": 18,
        "status": "Activo",
    },
    {
        "name": "Leche entera 1L",
        "category": "Lacteos",
        "price": 4300,
        "stock": 9,
        "status": "Activo",
    },
    {
        "name": "Cafe molido 250g",
        "category": "Bebidas",
        "price": 12500,
        "stock": 15,
        "status": "Activo",
    },
]


class ProductModel:
    def __init__(self, store_id=None):
        self.db = Database.get_instance()
        self.store_id = store_id

    def set_store_id(self, store_id):
        self.store_id = int(store_id) if store_id else None

    def sale_model(self):
        from models.sale_model import SaleModel

        return SaleModel()

    def initialize_defaults(self):
        if not self.db.ensure_connected():
            return

        self._ensure_support_rows()
        count = self.db.fetch_one("SELECT COUNT(*) AS total FROM TProductos")
        if not count or count["total"] > 0:
            return

        for product in SEED_PRODUCTS:
            self.db.execute_query(
                """
                INSERT INTO TProductos
                    (
                        nTiendaFK,
                        cDescripcionCorta,
                        cDescripcionLarga,
                        nCategoriaFK,
                        jEspecificaciones,
                        nPrecioUnitario,
                        nCantidadStock
                    )
                VALUES (%s, %s, %s, %s, '{}', %s, %s)
                """,
                (
                    self._default_store_id(),
                    product["name"],
                    product["name"],
                    self._category_id(product["category"]),
                    product["price"],
                    product["stock"],
                ),
            )

    def get_all_products(self):
        if _API:
            data = _API.get_products(self.store_id)
            if not data:
                return []
            # map API fields to expected normalized format
            def map_row(r):
                row = {
                    "id": r.get("nProductoID") or r.get("id"),
                    "name": r.get("cDescripcionCorta") or r.get("name"),
                    "category": r.get("cNombreCategoria") or r.get("category"),
                    "price": float(r.get("nPrecioUnitario") or r.get("price") or 0),
                    "stock": int(r.get("nCantidadStock") or r.get("stock") or 0),
                    "status": "Activo",
                }
                return row

            return [map_row(r) for r in data]

        if not self.db.ensure_connected():
            return []

        query = self._product_select()
        params = ()
        if self.store_id:
            query += " WHERE p.nTiendaFK = %s"
            params = (self.store_id,)
        rows = self.db.fetch_all(query + " ORDER BY name", params)
        return [self._normalize(row) for row in rows]

    def get_product(self, product_id):
        product_id = int(product_id)
        if _API:
            r = _API.get_product(product_id)
            if not r:
                return None
            mapped = {
                "id": r.get("nProductoID") or r.get("id"),
                "name": r.get("cDescripcionCorta") or r.get("name"),
                "category": r.get("cNombreCategoria") or r.get("category"),
                "price": float(r.get("nPrecioUnitario") or r.get("price") or 0),
                "stock": int(r.get("nCantidadStock") or r.get("stock") or 0),
                "status": "Activo",
            }
            return mapped

        if not self.db.ensure_connected():
            return None

        params = [product_id]
        store_filter = ""
        if self.store_id:
            store_filter = " AND p.nTiendaFK = %s"
            params.append(self.store_id)
        row = self.db.fetch_one(
            self._product_select() + " WHERE p.nProductoID = %s" + store_filter,
            tuple(params),
        )
        return self._normalize(row) if row else None

    def create_product(self, name, category, price, stock):
        name = (name or "").strip()
        category = (category or "").strip()
        price = float(price or 0)
        stock = int(stock or 0)
        if not name or not category:
            return False
        # If API mode, create product via API (requires worker token)
        if _API:
            data = {
                "nTiendaFK": self._active_store_id(),
                "cDescripcionCorta": name,
                "cDescripcionLarga": name,
                "nCategoriaFK": None,
                "jEspecificaciones": None,
                "nPrecioUnitario": price,
                "nCantidadStock": stock,
            }
            ok, resp = _API.create_product(data)
            return ok

        if not self.db.ensure_connected():
            return False

        self._ensure_support_rows()
        cursor = self.db.execute_query(
            """
            INSERT INTO TProductos
                (
                    nTiendaFK,
                    cDescripcionCorta,
                    cDescripcionLarga,
                    nCategoriaFK,
                    jEspecificaciones,
                    nPrecioUnitario,
                    nCantidadStock
                )
            VALUES (%s, %s, %s, %s, '{}', %s, %s)
            """,
            (
                self._active_store_id(),
                name,
                name,
                self._category_id(category),
                price,
                stock,
            ),
        )
        return cursor is not None

    def adjust_stock(self, product_id, delta):
        product_id = int(product_id)
        delta = int(delta)
        if _API:
            # For simplicity, read current product and compute new stock
            prod = self.get_product(product_id)
            if not prod:
                return False
            new_stock = max(0, int(prod.get("stock", 0)) + delta)
            ok, resp = _API.update_stock(product_id, new_stock)
            return ok

        if not self.db.ensure_connected():
            return False

        cursor = self.db.execute_query(
            """
            UPDATE TProductos
            SET nCantidadStock = GREATEST(COALESCE(nCantidadStock, 0) + %s, 0)
            WHERE nProductoID = %s
            """,
            (delta, product_id),
        )
        return cursor is not None

    def low_stock(self, threshold=10):
        return [
            product
            for product in self.get_all_products()
            if int(product["stock"]) <= threshold
        ]

    def inventory_summary(self):
        products = self.get_all_products()
        total_products = len(products)
        total_units = sum(int(product["stock"]) for product in products)
        inventory_value = sum(
            float(product["price"]) * int(product["stock"]) for product in products
        )
        return {
            "total_products": total_products,
            "total_units": total_units,
            "inventory_value": inventory_value,
            "low_stock": len(self.low_stock()),
        }

    def _ensure_support_rows(self):
        if not self.db.fetch_one("SELECT nCategoriaID FROM TCategoria LIMIT 1"):
            self.db.execute_query(
                """
                INSERT INTO TCategoria
                    (cNombreCategoria, nCategoriaPadreFK, bEstado)
                VALUES ('General', NULL, 1)
                """
            )
        if not self.db.fetch_one("SELECT nTiendaID FROM TTiendas LIMIT 1"):
            self.db.execute_query(
                """
                INSERT INTO TTiendas
                    (cNombreComercial, tDescripcion, eEstadoTienda)
                VALUES ('MercadoShop', 'Tienda principal', 'Activa')
                """
            )

    def _category_id(self, category):
        category = (category or "General").strip() or "General"
        row = self.db.fetch_one(
            "SELECT nCategoriaID FROM TCategoria WHERE cNombreCategoria = %s LIMIT 1",
            (category,),
        )
        if row:
            return row["nCategoriaID"]

        cursor = self.db.execute_query(
            """
            INSERT INTO TCategoria
                (cNombreCategoria, nCategoriaPadreFK, bEstado)
            VALUES (%s, NULL, 1)
            """,
            (category,),
        )
        return cursor.lastrowid if cursor else self._default_category_id()

    def _default_category_id(self):
        row = self.db.fetch_one("SELECT nCategoriaID FROM TCategoria LIMIT 1")
        return row["nCategoriaID"] if row else None

    def _default_store_id(self):
        row = self.db.fetch_one("SELECT nTiendaID FROM TTiendas LIMIT 1")
        return row["nTiendaID"] if row else None

    def _active_store_id(self):
        return self.store_id or self._default_store_id()

    def _product_select(self):
        return """
            SELECT
                p.nProductoID AS id,
                COALESCE(
                    NULLIF(p.cDescripcionCorta, ''),
                    NULLIF(p.cDescripcionLarga, ''),
                    CONCAT('Producto ', p.nProductoID)
                ) AS name,
                COALESCE(c.cNombreCategoria, 'General') AS category,
                COALESCE(p.nPrecioUnitario, 0) AS price,
                COALESCE(p.nCantidadStock, 0) AS stock,
                'Activo' AS status
            FROM TProductos p
            LEFT JOIN TCategoria c ON c.nCategoriaID = p.nCategoriaFK
        """

    @staticmethod
    def _normalize(row):
        normalized = dict(row)
        if isinstance(normalized.get("price"), Decimal):
            normalized["price"] = float(normalized["price"])
        return normalized
