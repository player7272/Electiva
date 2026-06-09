package com.tuuniversidad.ecosistema.view

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.tuuniversidad.ecosistema.R
import com.tuuniversidad.ecosistema.model.CarritoItem

class CarritoAdapter(
    private var items: List<CarritoItem>,
    private val onIncrementar: (Int) -> Unit,
    private val onDecrementar: (Int) -> Unit,
    private val onEliminar: (Int) -> Unit
) : RecyclerView.Adapter<CarritoAdapter.CarritoViewHolder>() {

    inner class CarritoViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val tvNombre: TextView    = itemView.findViewById(R.id.tvCarritoNombre)
        val tvPrecio: TextView    = itemView.findViewById(R.id.tvCarritoPrecio)
        val tvCantidad: TextView  = itemView.findViewById(R.id.tvCarritoCantidad)
        val tvSubtotal: TextView  = itemView.findViewById(R.id.tvCarritoSubtotal)
        val btnMas: Button        = itemView.findViewById(R.id.btnMas)
        val btnMenos: Button      = itemView.findViewById(R.id.btnMenos)
        val btnEliminar: Button   = itemView.findViewById(R.id.btnEliminarItem)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CarritoViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_carrito, parent, false)
        return CarritoViewHolder(view)
    }

    override fun onBindViewHolder(holder: CarritoViewHolder, position: Int) {
        val item = items[position]
        val id   = item.producto.nProductoID

        holder.tvNombre.text   = item.producto.cDescripcionCorta
        holder.tvPrecio.text   = "$ ${String.format("%,.0f", item.producto.nPrecioUnitario)} c/u"
        holder.tvCantidad.text = "Cantidad: ${item.cantidad}"
        holder.tvSubtotal.text = "Subtotal: $ ${String.format("%,.0f", item.subtotal())}"

        holder.btnMas.setOnClickListener      { onIncrementar(id) }
        holder.btnMenos.setOnClickListener    { onDecrementar(id) }
        holder.btnEliminar.setOnClickListener { onEliminar(id) }
    }

    override fun getItemCount(): Int = items.size

    fun actualizarItems(nuevosItems: List<CarritoItem>) {
        items = nuevosItems
        notifyDataSetChanged()
    }
}
