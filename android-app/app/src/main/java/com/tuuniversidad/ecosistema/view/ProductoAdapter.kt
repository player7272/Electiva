package com.tuuniversidad.ecosistema.view

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.tuuniversidad.ecosistema.R
import com.tuuniversidad.ecosistema.model.Producto

class ProductoAdapter(
    private var productos: List<Producto>,
    private val onAgregarClick: (Producto) -> Unit
) : RecyclerView.Adapter<ProductoAdapter.ProductoViewHolder>() {

    inner class ProductoViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val tvNombre: TextView    = itemView.findViewById(R.id.tvNombreProducto)
        val tvPrecio: TextView    = itemView.findViewById(R.id.tvPrecioProducto)
        val tvStock: TextView     = itemView.findViewById(R.id.tvStockProducto)
        val tvCategoria: TextView = itemView.findViewById(R.id.tvCategoriaProducto)
        val btnAgregar: Button    = itemView.findViewById(R.id.btnAgregarCarrito)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductoViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_producto, parent, false)
        return ProductoViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProductoViewHolder, position: Int) {
        val producto = productos[position]

        holder.tvNombre.text    = producto.cDescripcionCorta
        holder.tvPrecio.text    = "$ ${String.format("%,.0f", producto.nPrecioUnitario)}"
        holder.tvStock.text     = "Stock: ${producto.nCantidadStock} unidades"
        holder.tvCategoria.text = producto.cNombreCategoria ?: "Sin categoría"

        holder.btnAgregar.isEnabled = producto.nCantidadStock > 0
        holder.btnAgregar.text = if (producto.nCantidadStock > 0) "Agregar" else "Sin stock"

        holder.btnAgregar.setOnClickListener {
            onAgregarClick(producto)
        }
    }

    override fun getItemCount(): Int = productos.size

    fun actualizarProductos(nuevosProductos: List<Producto>) {
        productos = nuevosProductos
        notifyDataSetChanged()
    }
}
