import os
import requests
from typing import Optional, Dict, Any


class ApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL") or "http://127.0.0.1:8080"
        self.token: Optional[str] = None

    def set_token(self, token: Optional[str]):
        self.token = token

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = extra.copy() if extra else {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get(self, path: str, params: Optional[Dict[str, Any]] = None):
        r = requests.get(self._url(path), params=params, headers=self._headers(), timeout=5)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, json_payload: Dict[str, Any]):
        r = requests.post(self._url(path), json=json_payload, headers=self._headers({"Content-Type": "application/json"}), timeout=5)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, json_payload: Dict[str, Any]):
        r = requests.put(self._url(path), json=json_payload, headers=self._headers({"Content-Type": "application/json"}), timeout=5)
        r.raise_for_status()
        return r.json()

    # Higher level helpers
    def get_products(self, store_id: Optional[int] = None):
        params = {}
        if store_id:
            params["tienda"] = store_id
        try:
            payload = self.get("/api/productos", params=params)
            return payload.get("data") if isinstance(payload, dict) else payload
        except Exception:
            return []

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        try:
            payload = self.get(f"/api/productos/{product_id}")
            return payload.get("data") if isinstance(payload, dict) else payload
        except Exception:
            return None

    def create_product(self, data: Dict[str, Any]):
        try:
            return True, self.post("/api/productos", data)
        except Exception as exc:
            return False, str(exc)

    def update_stock(self, product_id: int, nCantidadStock: int):
        try:
            return True, self.put(f"/api/productos/{product_id}/stock", {"nCantidadStock": nCantidadStock})
        except Exception as exc:
            return False, str(exc)

    def create_order(self, product_id: int, quantity: int, customer: str, store_id: Optional[int] = None):
        cliente = {"cNombre": customer}
        direccionEnvio = {"cNomenclatura": "Mostrador", "cNombreRecibidor": customer, "nMunicipioFK": 1}
        items = [{"nProductoID": int(product_id), "nCantidad": int(quantity)}]
        payload = {"cliente": cliente, "direccionEnvio": direccionEnvio, "items": items, "nCostoEnvio": 0}
        try:
            return True, self.post("/api/pedidos", payload)
        except Exception as exc:
            return False, str(exc)

    def get_admin_tiendas(self):
        try:
            payload = self.get("/api/admin/tiendas")
            return payload.get("data") if isinstance(payload, dict) else payload
        except Exception:
            return []


# Singleton default client
default_api = ApiClient()

def get_api_client() -> ApiClient:
    return default_api
