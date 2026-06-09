package com.tuuniversidad.ecosistema.model

import com.google.gson.annotations.SerializedName

data class Producto(
    @SerializedName("nProductoID")
    val nProductoID: Int,

    @SerializedName("nTiendaFK")
    val nTiendaFK: Int,

    @SerializedName("nombreTienda")
    val nombreTienda: String?,

    @SerializedName("cDescripcionCorta")
    val cDescripcionCorta: String,

    @SerializedName("cDescripcionLarga")
    val cDescripcionLarga: String?,

    @SerializedName("cUrlImagenPrincipal")
    val cUrlImagenPrincipal: String?,

    @SerializedName("nCategoriaFK")
    val nCategoriaFK: Int?,

    @SerializedName("cNombreCategoria")
    val cNombreCategoria: String?,

    @SerializedName("nPrecioUnitario")
    val nPrecioUnitario: Double,

    @SerializedName("nCantidadStock")
    val nCantidadStock: Int
)
