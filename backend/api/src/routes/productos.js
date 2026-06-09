// src/routes/productos.js
const express = require('express');
const router = express.Router();
const { getProductos, getProductoById, actualizarStock, crearProducto } = require('../controllers/productosController');
const { trabajadorOnlyMiddleware } = require('../middleware/auth');

// Rutas PÚBLICAS (sin autenticación) - usadas por la app Android
router.get('/',    getProductos);       // GET /api/productos
router.get('/:id', getProductoById);    // GET /api/productos/:id

// Rutas PROTEGIDAS - solo trabajadores de tienda (app escritorio)
router.post('/',                trabajadorOnlyMiddleware, crearProducto);         // POST /api/productos
router.put('/:id/stock',        trabajadorOnlyMiddleware, actualizarStock);       // PUT /api/productos/:id/stock

module.exports = router;
