package com.tuuniversidad.ecosistema.network

import com.tuuniversidad.ecosistema.model.Producto
import com.google.gson.annotations.SerializedName
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

data class ProductosResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("total")   val total: Int,
    @SerializedName("data")    val data: List<Producto>
)

data class PedidoResponse(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String,
    @SerializedName("data")    val data: PedidoData?
)

data class PedidoData(
    @SerializedName("nPedidoID")          val nPedidoID: Int,
    @SerializedName("cNumeroComprobante") val cNumeroComprobante: String,
    @SerializedName("nTotal")             val nTotal: Double
)

data class ClienteRequest(
    val cNombre: String,
    val cApellido: String,
    val cDocumento: String,
    val cCorreo: String,
    val cTelefono: String
)

data class DireccionEnvioRequest(
    val cNomenclatura: String,
    val cBarrio: String,
    val cNotasAdicionales: String,
    val cCodigoPostal: String,
    val nMunicipioFK: Int,
    val cNombreRecibidor: String,
    val cTelefonoRecibidor: String
)

data class PedidoItemRequest(
    val nProductoID: Int,
    val nCantidad: Int
)

data class CrearPedidoRequest(
    val cliente: ClienteRequest,
    val direccionEnvio: DireccionEnvioRequest,
    val items: List<PedidoItemRequest>,
    val nCostoEnvio: Double
)

interface ApiService {
    @GET("api/productos")
    fun getProductos(): Call<ProductosResponse>

    @POST("api/pedidos")
    fun crearPedido(@Body request: CrearPedidoRequest): Call<PedidoResponse>
}
