from models.product_model import ProductModel


class InventoryController:
    def __init__(self):
        self.products = ProductModel()

    def set_store_id(self, store_id):
        self.products.set_store_id(store_id)

    def list_products(self):
        return self.products.get_all_products()

    def summary(self):
        return self.products.inventory_summary()

    def low_stock(self):
        return self.products.low_stock()

    def create_product(self, name, category, price, stock):
        try:
            created = self.products.create_product(name, category, price, stock)
        except ValueError:
            return False, "Precio y stock deben ser numericos."
        if created:
            return True, "Producto creado."
        return False, "Revisa los datos del producto."

    def adjust_stock(self, product_id, delta):
        try:
            updated = self.products.adjust_stock(product_id, delta)
        except ValueError:
            return False, "El ajuste debe ser numerico."
        if updated:
            return True, "Stock actualizado."
        return False, "No se pudo actualizar el stock."
