package com.tuuniversidad.ecosistema.controller

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.tuuniversidad.ecosistema.R
import com.tuuniversidad.ecosistema.model.CarritoManager
import com.tuuniversidad.ecosistema.network.ClienteRequest
import com.tuuniversidad.ecosistema.network.CrearPedidoRequest
import com.tuuniversidad.ecosistema.network.DireccionEnvioRequest
import com.tuuniversidad.ecosistema.network.PedidoItemRequest
import com.tuuniversidad.ecosistema.network.PedidoResponse
import com.tuuniversidad.ecosistema.network.RetrofitClient
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class CheckoutActivity : AppCompatActivity() {

    private val NUMERO_WHATSAPP_TIENDA = "573001234567"

    private lateinit var etNombre: EditText
    private lateinit var etApellido: EditText
    private lateinit var etDocumento: EditText
    private lateinit var etCorreo: EditText
    private lateinit var etTelefono: EditText
    private lateinit var etNomenclatura: EditText
    private lateinit var etBarrio: EditText
    private lateinit var etNotas: EditText
    private lateinit var tvResumenTotal: TextView
    private lateinit var btnConfirmar: Button
    private lateinit var progressBar: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_checkout)

        etNombre         = findViewById(R.id.etNombre)
        etApellido       = findViewById(R.id.etApellido)
        etDocumento      = findViewById(R.id.etDocumento)
        etCorreo         = findViewById(R.id.etCorreo)
        etTelefono       = findViewById(R.id.etTelefono)
        etNomenclatura   = findViewById(R.id.etNomenclatura)
        etBarrio         = findViewById(R.id.etBarrio)
        etNotas          = findViewById(R.id.etNotas)
        tvResumenTotal   = findViewById(R.id.tvResumenTotal)
        btnConfirmar     = findViewById(R.id.btnConfirmarPedido)
        progressBar      = findViewById(R.id.progressBarCheckout)

        tvResumenTotal.text = "Total a pagar: $ ${String.format("%,.0f", CarritoManager.getTotal())}"

        btnConfirmar.setOnClickListener {
            if (validarFormulario()) {
                enviarPedidoAlBackend()
            }
        }
    }

    private fun validarFormulario(): Boolean {
        val campos = listOf(
            Pair(etNombre,       "Nombre"),
            Pair(etApellido,     "Apellido"),
            Pair(etDocumento,    "Documento"),
            Pair(etTelefono,     "Teléfono"),
            Pair(etNomenclatura, "Dirección (Nomenclatura)"),
            Pair(etBarrio,       "Barrio")
        )

        for ((campo, nombre) in campos) {
            if (campo.text.toString().trim().isEmpty()) {
                campo.error = "El campo $nombre es obligatorio"
                campo.requestFocus()
                return false
            }
        }
        return true
    }

    private fun enviarPedidoAlBackend() {
        btnConfirmar.isEnabled = false
        progressBar.visibility = View.VISIBLE

        val clienteReq = ClienteRequest(
            cNombre    = etNombre.text.toString().trim(),
            cApellido  = etApellido.text.toString().trim(),
            cDocumento = etDocumento.text.toString().trim(),
            cCorreo    = etCorreo.text.toString().trim().ifEmpty { "sin_correo@temp.co" },
            cTelefono  = etTelefono.text.toString().trim()
        )

        val direccionReq = DireccionEnvioRequest(
            cNomenclatura     = etNomenclatura.text.toString().trim(),
            cBarrio           = etBarrio.text.toString().trim(),
            cNotasAdicionales = etNotas.text.toString().trim(),
            cCodigoPostal     = "",
            nMunicipioFK      = 1,
            cNombreRecibidor  = "${clienteReq.cNombre} ${clienteReq.cApellido}",
            cTelefonoRecibidor = clienteReq.cTelefono
        )

        val itemsReq = CarritoManager.getItems().map { item ->
            PedidoItemRequest(
                nProductoID = item.producto.nProductoID,
                nCantidad   = item.cantidad
            )
        }

        val pedidoReq = CrearPedidoRequest(
            cliente       = clienteReq,
            direccionEnvio = direccionReq,
            items         = itemsReq,
            nCostoEnvio   = CarritoManager.getCostoEnvio()
        )

        val textoWhatsApp = CarritoManager.generarTextoWhatsApp(
            nombreCliente = "${clienteReq.cNombre} ${clienteReq.cApellido}",
            direccion     = "${direccionReq.cNomenclatura}, ${direccionReq.cBarrio}. ${direccionReq.cNotasAdicionales}",
            telefono      = clienteReq.cTelefono
        )

        RetrofitClient.apiService.crearPedido(pedidoReq).enqueue(object : Callback<PedidoResponse> {

            override fun onResponse(call: Call<PedidoResponse>, response: Response<PedidoResponse>) {
                progressBar.visibility = View.GONE
                btnConfirmar.isEnabled = true

                if (response.isSuccessful && response.body()?.success == true) {
                    val pedidoData = response.body()!!.data
                    Toast.makeText(
                        this@CheckoutActivity,
                        "¡Pedido ${pedidoData?.cNumeroComprobante} registrado con éxito!",
                        Toast.LENGTH_LONG
                    ).show()

                    CarritoManager.limpiar()

                    abrirWhatsApp(textoWhatsApp)

                } else {
                    val errorMsg = response.errorBody()?.string() ?: "Error desconocido"
                    Toast.makeText(
                        this@CheckoutActivity,
                        "Error al registrar pedido: $errorMsg",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }

            override fun onFailure(call: Call<PedidoResponse>, t: Throwable) {
                progressBar.visibility = View.GONE
                btnConfirmar.isEnabled = true
                Toast.makeText(
                    this@CheckoutActivity,
                    "Error de red: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        })
    }

    private fun abrirWhatsApp(texto: String) {
        val textoEncoded = Uri.encode(texto)
        val url = "https://wa.me/$NUMERO_WHATSAPP_TIENDA?text=$textoEncoded"

        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
        intent.setPackage("com.whatsapp")

        try {
            startActivity(intent)
        } catch (e: android.content.ActivityNotFoundException) {
            val intentBrowser = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            startActivity(intentBrowser)
        }

        val intentMain = Intent(this, MainActivity::class.java)
        intentMain.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP
        startActivity(intentMain)
        finish()
    }
}
