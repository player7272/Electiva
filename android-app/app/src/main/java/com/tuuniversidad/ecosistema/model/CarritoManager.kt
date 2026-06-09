package com.tuuniversidad.ecosistema.model

data class CarritoItem(
    val producto: Producto,
    var cantidad: Int
) {
    fun subtotal(): Double = producto.nPrecioUnitario * cantidad
}

object CarritoManager {
    private val items: MutableList<CarritoItem> = mutableListOf()

    fun agregarProducto(producto: Producto) {
        val itemExistente = items.find { it.producto.nProductoID == producto.nProductoID }
        if (itemExistente != null) {
            if (itemExistente.cantidad < producto.nCantidadStock) {
                itemExistente.cantidad++
            }
        } else {
            items.add(CarritoItem(producto = producto, cantidad = 1))
        }
    }

    fun eliminarProducto(nProductoID: Int) {
        items.removeAll { it.producto.nProductoID == nProductoID }
    }

    fun incrementarCantidad(nProductoID: Int) {
        val item = items.find { it.producto.nProductoID == nProductoID }
        if (item != null && item.cantidad < item.producto.nCantidadStock) {
            item.cantidad++
        }
    }

    fun decrementarCantidad(nProductoID: Int) {
        val item = items.find { it.producto.nProductoID == nProductoID }
        if (item != null) {
            item.cantidad--
            if (item.cantidad <= 0) {
                eliminarProducto(nProductoID)
            }
        }
    }

    fun getItems(): List<CarritoItem> = items.toList()

    fun cantidadItems(): Int = items.size

    fun getSubtotal(): Double = items.sumOf { it.subtotal() }

    fun getCostoEnvio(): Double = 8000.0

    fun getTotal(): Double = getSubtotal() + getCostoEnvio()

    fun estaVacio(): Boolean = items.isEmpty()

    fun limpiar() { items.clear() }

    fun generarTextoWhatsApp(nombreCliente: String, direccion: String, telefono: String): String {
        val sb = StringBuilder()
        sb.appendLine("🛒 *NUEVO PEDIDO*")
        sb.appendLine("─────────────────────")
        sb.appendLine("👤 *Cliente:* $nombreCliente")
        sb.appendLine("📱 *Teléfono:* $telefono")
        sb.appendLine("📍 *Dirección:* $direccion")
        sb.appendLine("─────────────────────")
        sb.appendLine("📦 *PRODUCTOS:")

        for (item in items) {
            val subtotalItem = item.subtotal()
            sb.appendLine("• ${item.producto.cDescripcionCorta} x${item.cantidad} = $${formatearPrecio(subtotalItem)}")
        }

        sb.appendLine("─────────────────────")
        sb.appendLine("💰 *Subtotal:* $${formatearPrecio(getSubtotal())}")
        sb.appendLine("🚚 *Envío:* $${formatearPrecio(getCostoEnvio())}")
        sb.appendLine("✅ *TOTAL: $${formatearPrecio(getTotal())}*")
        sb.appendLine("─────────────────────")
        sb.appendLine("_Pedido generado desde la App Móvil_")

        return sb.toString()
    }

    private fun formatearPrecio(valor: Double): String {
        return String.format("%,.0f", valor)
    }
}
