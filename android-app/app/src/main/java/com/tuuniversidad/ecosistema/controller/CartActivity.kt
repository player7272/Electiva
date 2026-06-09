package com.tuuniversidad.ecosistema.controller

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.tuuniversidad.ecosistema.R
import com.tuuniversidad.ecosistema.model.CarritoManager
import com.tuuniversidad.ecosistema.view.CarritoAdapter

class CartActivity : AppCompatActivity() {

    private lateinit var recyclerCarrito: RecyclerView
    private lateinit var tvSubtotal: TextView
    private lateinit var tvEnvio: TextView
    private lateinit var tvTotal: TextView
    private lateinit var btnProcederPago: Button
    private lateinit var tvCarritoVacio: TextView

    private lateinit var carritoAdapter: CarritoAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_cart)

        recyclerCarrito  = findViewById(R.id.recyclerCarrito)
        tvSubtotal       = findViewById(R.id.tvSubtotal)
        tvEnvio          = findViewById(R.id.tvEnvio)
        tvTotal          = findViewById(R.id.tvTotal)
        btnProcederPago  = findViewById(R.id.btnProcederPago)
        tvCarritoVacio   = findViewById(R.id.tvCarritoVacio)

        recyclerCarrito.layoutManager = LinearLayoutManager(this)

        carritoAdapter = CarritoAdapter(
            items = CarritoManager.getItems(),
            onIncrementar = { productoID ->
                CarritoManager.incrementarCantidad(productoID)
                refrescarCarrito()
            },
            onDecrementar = { productoID ->
                CarritoManager.decrementarCantidad(productoID)
                refrescarCarrito()
            },
            onEliminar = { productoID ->
                CarritoManager.eliminarProducto(productoID)
                refrescarCarrito()
            }
        )
        recyclerCarrito.adapter = carritoAdapter

        btnProcederPago.setOnClickListener {
            if (CarritoManager.estaVacio()) {
                Toast.makeText(this, "El carrito está vacío.", Toast.LENGTH_SHORT).show()
            } else {
                startActivity(Intent(this, CheckoutActivity::class.java))
            }
        }

        refrescarCarrito()
    }

    override fun onResume() {
        super.onResume()
        refrescarCarrito()
    }

    private fun refrescarCarrito() {
        val items = CarritoManager.getItems()

        if (items.isEmpty()) {
            tvCarritoVacio.visibility = android.view.View.VISIBLE
            recyclerCarrito.visibility = android.view.View.GONE
            btnProcederPago.isEnabled = false
        } else {
            tvCarritoVacio.visibility = android.view.View.GONE
            recyclerCarrito.visibility = android.view.View.VISIBLE
            btnProcederPago.isEnabled = true
            carritoAdapter.actualizarItems(items)
        }

        tvSubtotal.text = "Subtotal: $ ${String.format("%,.0f", CarritoManager.getSubtotal())}"
        tvEnvio.text    = "Envío: $ ${String.format("%,.0f", CarritoManager.getCostoEnvio())}"
        tvTotal.text    = "TOTAL: $ ${String.format("%,.0f", CarritoManager.getTotal())}"
    }
}
