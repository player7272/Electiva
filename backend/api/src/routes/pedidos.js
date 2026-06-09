// src/routes/pedidos.js
const express = require('express');
const router = express.Router();
const { crearPedido, getPedidos, actualizarEstadoPedido } = require('../controllers/pedidosController');
const { trabajadorOnlyMiddleware } = require('../middleware/auth');

// POST /api/pedidos - PÚBLICO (app móvil Android, sin login de cliente requerido)
router.post('/', crearPedido);

// GET /api/pedidos - PROTEGIDO (app de escritorio para validar comprobantes)
router.get('/', trabajadorOnlyMiddleware, getPedidos);

// PATCH /api/pedidos/:id/estado - PROTEGIDO (app de escritorio)
router.patch('/:id/estado', trabajadorOnlyMiddleware, actualizarEstadoPedido);

module.exports = router;
