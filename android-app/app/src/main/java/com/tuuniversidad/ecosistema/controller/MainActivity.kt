package com.tuuniversidad.ecosistema.controller

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.tuuniversidad.ecosistema.R
import com.tuuniversidad.ecosistema.model.CarritoManager
import com.tuuniversidad.ecosistema.model.Producto
import com.tuuniversidad.ecosistema.network.ProductosResponse
import com.tuuniversidad.ecosistema.network.RetrofitClient
import com.tuuniversidad.ecosistema.view.ProductoAdapter
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class MainActivity : AppCompatActivity() {

    private lateinit var recyclerProductos: RecyclerView
    private lateinit var progressBar: ProgressBar
    private lateinit var tvError: TextView
    private lateinit var btnVerCarrito: Button
    private lateinit var tvContadorCarrito: TextView
    private lateinit var productoAdapter: ProductoAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        recyclerProductos  = findViewById(R.id.recyclerProductos)
        progressBar        = findViewById(R.id.progressBar)
        tvError            = findViewById(R.id.tvError)
        btnVerCarrito      = findViewById(R.id.btnVerCarrito)
        tvContadorCarrito  = findViewById(R.id.tvContadorCarrito)

        recyclerProductos.layoutManager = LinearLayoutManager(this)

        productoAdapter = ProductoAdapter(
            productos = emptyList(),
            onAgregarClick = { producto ->
                CarritoManager.agregarProducto(producto)
                actualizarContadorCarrito()
                Toast.makeText(this, "\"${producto.cDescripcionCorta}\" agregado al carrito", Toast.LENGTH_SHORT).show()
            }
        )
        recyclerProductos.adapter = productoAdapter

        btnVerCarrito.setOnClickListener {
            if (CarritoManager.estaVacio()) {
                Toast.makeText(this, "El carrito está vacío. Agrega productos primero.", Toast.LENGTH_SHORT).show()
            } else {
                startActivity(Intent(this, CartActivity::class.java))
            }
        }

        cargarProductos()
    }

    override fun onResume() {
        super.onResume()
        actualizarContadorCarrito()
    }

    private fun cargarProductos() {
        progressBar.visibility = View.VISIBLE
        tvError.visibility = View.GONE
        recyclerProductos.visibility = View.GONE

        RetrofitClient.apiService.getProductos().enqueue(object : Callback<ProductosResponse> {

            override fun onResponse(call: Call<ProductosResponse>, response: Response<ProductosResponse>) {
                progressBar.visibility = View.GONE

                if (response.isSuccessful && response.body()?.success == true) {
                    val productos = response.body()!!.data
                    if (productos.isEmpty()) {
                        mostrarError("No hay productos disponibles en este momento.")
                    } else {
                        recyclerProductos.visibility = View.VISIBLE
                        productoAdapter.actualizarProductos(productos)
                    }
                } else {
                    mostrarError("Error del servidor: ${response.code()}. Intenta de nuevo.")
                }
            }

            override fun onFailure(call: Call<ProductosResponse>, t: Throwable) {
                progressBar.visibility = View.GONE
                mostrarError("Error de conexión: ${t.message}\n\nVerifica que el servidor esté corriendo y la IP sea correcta.")
            }
        })
    }

    private fun mostrarError(mensaje: String) {
        tvError.text = mensaje
        tvError.visibility = View.VISIBLE
        recyclerProductos.visibility = View.GONE
    }

    private fun actualizarContadorCarrito() {
        val cantidad = CarritoManager.cantidadItems()
        tvContadorCarrito.text = if (cantidad > 0) "($cantidad)" else ""
    }
}
