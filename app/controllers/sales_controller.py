from models.product_model import ProductModel
from models.sale_model import SaleModel


class SalesController:
    def __init__(self):
        self.products = ProductModel()
        self.sales = SaleModel()
        self.store_id = None

    def set_store_id(self, store_id):
        self.store_id = int(store_id) if store_id else None
        self.products.set_store_id(self.store_id)
        self.sales.set_store_id(self.store_id)

    def list_products(self):
        return self.products.get_all_products()

    def recent_sales(self):
        return self.sales.recent_sales()

    def list_orders(self):
        return self.sales.list_orders()

    def list_states(self):
        return self.sales.list_states()

    def approve_order(self, order_id):
        try:
            return self.sales.approve_order(order_id)
        except ValueError:
            return False, "Pedido no valido."

    def update_order_state(self, order_id, state_id):
        try:
            return self.sales.update_order_state(order_id, state_id)
        except ValueError:
            return False, "Estado no valido."

    def create_sale(self, product_id, quantity, customer):
        try:
            return self.sales.create_sale(product_id, quantity, customer)
        except ValueError:
            return False, "Producto y cantidad deben ser validos."
