from datetime import datetime
from decimal import Decimal

from models.database import Error, Database
from models.product_model import ProductModel
import os
from api_client import get_api_client

_USE_API = str(os.getenv("USE_API", "0")).lower() in ("1", "true", "yes")
_API = get_api_client() if _USE_API else None


APPROVED_PAYMENT_STATES = {
    "APPROVED",
    "APROBADO",
    "PAID",
    "PAGADO",
    "COMPLETED",
    "CAPTURED",
}
PENDING_ORDER_STATES = {"", "pendiente de pago", "registrado", "sin estado"}
APPROVED_ORDER_STATE = "Pago Confirmado"
DEFAULT_ORDER_STATES = (
    "Pendiente de Pago",
    "Pago Confirmado",
    "En Preparacion",
    "Enviado",
    "Entregado",
    "Cancelado",
)


class SaleModel:
    def __init__(self, store_id=None):
        self.db = Database.get_instance()
        self.store_id = int(store_id) if store_id else None
        self.products = ProductModel(store_id=self.store_id)

    def set_store_id(self, store_id):
        self.store_id = int(store_id) if store_id else None
        self.products.set_store_id(self.store_id)

    def list_orders(self, limit=50):
        # If API available and token set, use API to list pedidos (protected)
        if _API:
            try:
                params = {"limit": int(limit)}
                # API supports 'comprobante' query but not limit param; we reuse limit via client if needed
                data = _API.get("/api/pedidos")
                rows = data.get("data") if isinstance(data, dict) else data
                return [self._normalize(row) for row in rows]
            except Exception:
                # fallback to DB
                pass

        if not self.db.ensure_connected():
            return []

        detail_filter = ""
        params = []
        if self.store_id:
            detail_filter = "WHERE prod.nTiendaFK = %s"
            params.append(self.store_id)

        params.append(int(limit))
        rows = self.db.fetch_all(
            f"""
            SELECT
                p.nPedidoID AS id,
                COALESCE(detail.store_name, 'Tienda') AS store_name,
                COALESCE(
                    NULLIF(
                        TRIM(CONCAT(COALESCE(u.cNombre, ''), ' ', COALESCE(u.cApellido, ''))),
                        ''
                    ),
                    'Cliente mostrador'
                ) AS customer,
                COALESCE(p.cNumeroComprobante, '') AS receipt,
                COALESCE(p.nSubtotal, 0) AS subtotal,
                COALESCE(p.nCostoEnvio, 0) AS shipping,
                COALESCE(p.nTotal, 0) AS total,
                ep.nEstadoPedidoID AS state_id,
                COALESCE(ep.cNombreEstado, 'Sin estado') AS state,
                DATE_FORMAT(COALESCE(p.dFechaActualizacion, CURRENT_TIMESTAMP), '%Y-%m-%d %H:%i') AS created_at,
                COALESCE(detail.items, 'Sin detalle') AS items,
                COALESCE(tx_id.cNombrePasarela, tx_order.cNombrePasarela, '') AS payment_gateway,
                COALESCE(tx_id.cIdTransaccionExterna, tx_order.cIdTransaccionExterna, '') AS payment_reference,
                COALESCE(tx_id.cMetodoPago, tx_order.cMetodoPago, '') AS payment_method,
                COALESCE(tx_id.eFranquicia, tx_order.eFranquicia, '') AS payment_brand,
                COALESCE(tx_id.cUltimos4Digitos, tx_order.cUltimos4Digitos, '') AS payment_last4,
                COALESCE(tx_id.nCuotas, tx_order.nCuotas, '') AS payment_installments,
                COALESCE(tx_id.nValorTransaccion, tx_order.nValorTransaccion, 0) AS payment_amount,
                COALESCE(tx_id.cEstadoTransaccion, tx_order.cEstadoTransaccion, '') AS payment_status,
                COALESCE(tx_id.cCodigoAprobacionBanco, tx_order.cCodigoAprobacionBanco, '') AS payment_authorization,
                COALESCE(CAST(tx_id.jRawResponse AS CHAR), CAST(tx_order.jRawResponse AS CHAR), '') AS payment_raw
            FROM TPedido p
            JOIN (
                SELECT
                    d.nPedidoFK,
                    GROUP_CONCAT(
                        CONCAT(
                            COALESCE(d.cNombreProducto, prod.cDescripcionCorta, 'Producto'),
                            ' x',
                            COALESCE(d.nCantidad, 0),
                            ' = ',
                            COALESCE(d.nSubtotal, 0)
                        )
                        ORDER BY d.nDetallePedidoID
                        SEPARATOR '\\n'
                    ) AS items,
                    GROUP_CONCAT(DISTINCT COALESCE(t.cNombreComercial, 'Tienda') SEPARATOR ', ') AS store_name
                FROM TDetallePedido d
                LEFT JOIN TProductos prod ON prod.nProductoID = d.nProductoFK
                LEFT JOIN TTiendas t ON t.nTiendaID = prod.nTiendaFK
                {detail_filter}
                GROUP BY d.nPedidoFK
            ) detail ON detail.nPedidoFK = p.nPedidoID
            LEFT JOIN TUsuarioCliente u ON u.nUsuarioClienteID = p.nClienteFK
            LEFT JOIN TEstadoPedido ep ON ep.nEstadoPedidoID = p.nEstadoPedidoFK
            LEFT JOIN TTransaccionPasarela tx_id
                ON tx_id.nTransaccionID = p.nTransaccionPasarelaFK
            LEFT JOIN (
                SELECT tx.*
                FROM TTransaccionPasarela tx
                INNER JOIN (
                    SELECT nPedidoFK, MAX(nTransaccionID) AS nTransaccionID
                    FROM TTransaccionPasarela
                    GROUP BY nPedidoFK
                ) latest ON latest.nTransaccionID = tx.nTransaccionID
            ) tx_order ON tx_order.nPedidoFK = p.nPedidoID
            ORDER BY COALESCE(p.dFechaActualizacion, CURRENT_TIMESTAMP) DESC
            LIMIT %s
            """,
            tuple(params),
        )
        return [self._normalize(row) for row in rows]

    def recent_sales(self, limit=10):
        orders = self.list_orders(max(int(limit), 10))
        sales = [
            order
            for order in orders
            if not self._is_pending_state(order.get("state"))
            and not self._is_state(order.get("state"), "Cancelado")
        ]
        return sales[:limit]

    def list_states(self):
        if self.db.ensure_connected():
            self._ensure_states()
            rows = self.db.fetch_all(
                """
                SELECT nEstadoPedidoID AS id, cNombreEstado AS name
                FROM TEstadoPedido
                ORDER BY nEstadoPedidoID
                """
            )
            if rows:
                return [{"id": row["id"], "name": row["name"]} for row in rows]
        return []

    def approve_order(self, order_id):
        # Prefer API call to update estado to 'Pago Confirmado' (ID likely 2)
        if _API:
            try:
                # ID 2 corresponds to 'Pago Confirmado' based on seeded defaults
                resp = _API.put(f"/api/pedidos/{int(order_id)}/estado", {"nEstadoPedidoFK": 2})
                return True, "Pedido aprobado via API."
            except Exception:
                pass

        if not self.db.ensure_connected():
            return False, "No se puede cargar la base de datos."
        return self._approve_order_in_database(order_id)

    def update_order_state(self, order_id, state_id):
        # Use API if available
        if _API:
            try:
                _API.put(f"/api/pedidos/{int(order_id)}/estado", {"nEstadoPedidoFK": int(state_id)})
                return True, "Estado actualizado via API."
            except Exception:
                pass

        if not self.db.ensure_connected():
            return False, "No se puede cargar la base de datos."

        target = self._state_by_id(state_id)
        if not target:
            return False, "Estado no valido."

        if self._is_approved_state(target["name"]):
            return self.approve_order(order_id)

        return self._update_order_state_in_database(order_id, target)

    def create_sale(self, product_id, quantity, customer):
        if _API:
            # Delegate order creation to backend API (public endpoint)
            try:
                ok, resp = _API.create_order(product_id, quantity, customer, self.store_id)
                if ok:
                    return True, "Venta registrada via API."
                return False, f"Error API: {resp}"
            except Exception as exc:
                return False, f"Error API: {exc}"

        if not self.db.ensure_connected():
            return False, "No se puede cargar la base de datos."

        product_id = int(product_id)
        quantity = int(quantity or 0)
        customer = (customer or "Cliente mostrador").strip() or "Cliente mostrador"
        if quantity <= 0:
            return False, "La cantidad debe ser mayor a cero."

        product = self.products.get_product(product_id)
        if not product:
            return False, "Producto no encontrado."
        if int(product["stock"]) < quantity:
            return False, "Stock insuficiente para la venta."

        price = float(product["price"])
        total = price * quantity

        return self._create_sale_in_database(product, quantity, customer, price, total)

    def _approve_order_in_database(self, order_id):
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            order = self._fetch_order_for_update(cursor, order_id)
            if not order:
                self.db.connection.rollback()
                return False, "Pedido no encontrado para esta tienda."
            if not self._payment_is_approved(order):
                self.db.connection.rollback()
                return False, "El pedido no tiene un pago aprobado."
            if not self._is_pending_state(order.get("state")):
                self.db.connection.rollback()
                return True, "El pedido ya esta aprobado; puedes actualizar su estado."

            approved_state_id = self._state_id_by_name(cursor, APPROVED_ORDER_STATE)
            items = self._fetch_order_items_for_update(cursor, order_id)
            if not items:
                self.db.connection.rollback()
                return False, "El pedido no tiene productos de esta tienda."

            for item in items:
                stock = int(item.get("stock") or 0)
                quantity = int(item.get("quantity") or 0)
                if stock < quantity:
                    self.db.connection.rollback()
                    return False, f"Stock insuficiente para {item['name']}."

            for item in items:
                cursor.execute(
                    """
                    UPDATE TProductos
                    SET nCantidadStock = nCantidadStock - %s
                    WHERE nProductoID = %s
                    """,
                    (item["quantity"], item["product_id"]),
                )

            cursor.execute(
                """
                UPDATE TPedido
                SET nEstadoPedidoFK = %s,
                    dFechaActualizacion = CURRENT_TIMESTAMP
                WHERE nPedidoID = %s
                """,
                (approved_state_id, int(order_id)),
            )
            self.db.connection.commit()
            return True, "Pedido aprobado y venta registrada."
        except Error as exc:
            print(f"Approve Order Error: {exc}")
            self.db.connection.rollback()
            return False, "No se pudo aprobar el pedido."
        finally:
            cursor.close()

    def _update_order_state_in_database(self, order_id, target):
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            order = self._fetch_order_for_update(cursor, order_id)
            if not order:
                self.db.connection.rollback()
                return False, "Pedido no encontrado para esta tienda."
            if self._is_pending_state(order.get("state")):
                self.db.connection.rollback()
                return False, "Primero aprueba el pedido para registrar la venta."

            cursor.execute(
                """
                UPDATE TPedido
                SET nEstadoPedidoFK = %s,
                    dFechaActualizacion = CURRENT_TIMESTAMP
                WHERE nPedidoID = %s
                """,
                (target["id"], int(order_id)),
            )
            self.db.connection.commit()
            return True, "Estado del pedido actualizado."
        except Error as exc:
            print(f"Update Order State Error: {exc}")
            self.db.connection.rollback()
            return False, "No se pudo actualizar el estado del pedido."
        finally:
            cursor.close()

    def _fetch_order_for_update(self, cursor, order_id):
        store_clause, params = self._store_exists_clause()
        cursor.execute(
            f"""
            SELECT
                p.nPedidoID AS id,
                p.nEstadoPedidoFK AS state_id,
                COALESCE(ep.cNombreEstado, '') AS state,
                COALESCE(tx_id.cEstadoTransaccion, tx_order.cEstadoTransaccion, '') AS payment_status,
                COALESCE(tx_id.cCodigoAprobacionBanco, tx_order.cCodigoAprobacionBanco, '') AS payment_authorization
            FROM TPedido p
            LEFT JOIN TEstadoPedido ep ON ep.nEstadoPedidoID = p.nEstadoPedidoFK
            LEFT JOIN TTransaccionPasarela tx_id
                ON tx_id.nTransaccionID = p.nTransaccionPasarelaFK
            LEFT JOIN (
                SELECT tx.*
                FROM TTransaccionPasarela tx
                INNER JOIN (
                    SELECT nPedidoFK, MAX(nTransaccionID) AS nTransaccionID
                    FROM TTransaccionPasarela
                    GROUP BY nPedidoFK
                ) latest ON latest.nTransaccionID = tx.nTransaccionID
            ) tx_order ON tx_order.nPedidoFK = p.nPedidoID
            WHERE p.nPedidoID = %s
            {store_clause}
            LIMIT 1
            FOR UPDATE
            """,
            (int(order_id), *params),
        )
        return cursor.fetchone()

    def _fetch_order_items_for_update(self, cursor, order_id):
        store_filter = ""
        params = [int(order_id)]
        if self.store_id:
            store_filter = "AND prod.nTiendaFK = %s"
            params.append(self.store_id)

        cursor.execute(
            f"""
            SELECT
                prod.nProductoID AS product_id,
                COALESCE(d.cNombreProducto, prod.cDescripcionCorta, 'Producto') AS name,
                COALESCE(d.nCantidad, 0) AS quantity,
                COALESCE(prod.nCantidadStock, 0) AS stock
            FROM TDetallePedido d
            JOIN TProductos prod ON prod.nProductoID = d.nProductoFK
            WHERE d.nPedidoFK = %s
            {store_filter}
            FOR UPDATE
            """,
            tuple(params),
        )
        return cursor.fetchall()

    def _store_exists_clause(self):
        if not self.store_id:
            return "", ()
        return (
            """
            AND EXISTS (
                SELECT 1
                FROM TDetallePedido d
                JOIN TProductos prod ON prod.nProductoID = d.nProductoFK
                WHERE d.nPedidoFK = p.nPedidoID
                  AND prod.nTiendaFK = %s
            )
            """,
            (self.store_id,),
        )

    def _create_sale_in_database(self, product, quantity, customer, price, total):
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT nCantidadStock
                FROM TProductos
                WHERE nProductoID = %s
                FOR UPDATE
                """,
                (product["id"],),
            )
            row = cursor.fetchone()
            if not row or int(row["nCantidadStock"] or 0) < quantity:
                self.db.connection.rollback()
                return False, "Stock insuficiente para la venta."

            customer_id = self._customer_id(cursor, customer)
            state_id = self._state_id_by_name(cursor, APPROVED_ORDER_STATE)
            receipt = f"MOSTRADOR-{datetime.now():%Y%m%d%H%M%S}"

            cursor.execute(
                """
                INSERT INTO TPedido
                    (
                        nClienteFK,
                        cNumeroComprobante,
                        nSubtotal,
                        nCostoEnvio,
                        nTotal,
                        nEstadoPedidoFK
                    )
                VALUES (%s, %s, %s, 0, %s, %s)
                """,
                (customer_id, receipt, total, total, state_id),
            )
            sale_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO TDetallePedido
                    (
                        nPedidoFK,
                        nProductoFK,
                        cNombreProducto,
                        nPrecioCompra,
                        nCantidad,
                        nSubtotal
                    )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (sale_id, product["id"], product["name"], price, quantity, total),
            )
            cursor.execute(
                """
                UPDATE TProductos
                SET nCantidadStock = nCantidadStock - %s
                WHERE nProductoID = %s
                """,
                (quantity, product["id"]),
            )
            self.db.connection.commit()
            return True, "Venta registrada."
        except Error as exc:
            print(f"Sale Error: {exc}")
            self.db.connection.rollback()
            return False, "No se pudo registrar la venta."
        finally:
            cursor.close()

    def _customer_id(self, cursor, customer):
        if customer.lower() in {"cliente mostrador", "mostrador"}:
            return None

        cursor.execute(
            """
            SELECT nUsuarioClienteID
            FROM TUsuarioCliente
            WHERE cNombre = %s
            ORDER BY nUsuarioClienteID
            LIMIT 1
            """,
            (customer,),
        )
        row = cursor.fetchone()
        if row:
            return row["nUsuarioClienteID"]

        cursor.execute(
            """
            INSERT INTO TUsuarioCliente
                (cNombre, cApellido, cDocumento, cContrasena, cCorreo, cTelefono)
            VALUES (%s, '', '', '', '', '')
            """,
            (customer,),
        )
        return cursor.lastrowid

    def _state_id_by_name(self, cursor, name):
        cursor.execute(
            """
            SELECT nEstadoPedidoID
            FROM TEstadoPedido
            WHERE cNombreEstado = %s
            LIMIT 1
            """,
            (name,),
        )
        row = cursor.fetchone()
        if row:
            return row["nEstadoPedidoID"]

        cursor.execute(
            "INSERT INTO TEstadoPedido (cNombreEstado) VALUES (%s)",
            (name,),
        )
        return cursor.lastrowid

    def _ensure_states(self):
        existing = {
            row["cNombreEstado"]
            for row in self.db.fetch_all("SELECT cNombreEstado FROM TEstadoPedido")
            if row.get("cNombreEstado")
        }
        for state in DEFAULT_ORDER_STATES:
            if state in existing:
                continue
            self.db.execute_query(
                "INSERT INTO TEstadoPedido (cNombreEstado) VALUES (%s)",
                (state,),
            )

    def _state_by_id(self, state_id):
        try:
            state_id = int(state_id)
        except (TypeError, ValueError):
            return None
        for state in self.list_states():
            if int(state["id"]) == state_id:
                return state
        return None

    @staticmethod
    def _payment_is_approved(order):
        status = str(order.get("payment_status") or "").strip().upper()
        return status in APPROVED_PAYMENT_STATES

    @staticmethod
    def _is_pending_state(state):
        return str(state or "").strip().lower() in PENDING_ORDER_STATES

    @staticmethod
    def _is_approved_state(state):
        return SaleModel._is_state(state, APPROVED_ORDER_STATE)

    @staticmethod
    def _is_state(current, expected):
        return str(current or "").strip().lower() == str(expected or "").strip().lower()

    @staticmethod
    def _normalize(row):
        normalized = dict(row)
        for key in ("subtotal", "shipping", "total", "payment_amount"):
            if isinstance(normalized.get(key), Decimal):
                normalized[key] = float(normalized[key])
        for key in ("payment_raw", "payment_installments"):
            if normalized.get(key) is None:
                normalized[key] = ""
        return normalized
