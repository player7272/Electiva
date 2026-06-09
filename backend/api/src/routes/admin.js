// src/routes/admin.js
const express = require('express');
const router = express.Router();
const {
  getTiendas,
  actualizarEstadoTienda,
  getAdmins,
  crearAdmin,
  actualizarEstadoAdmin,
  getRoles,
  getPQRS
} = require('../controllers/adminController');
const { adminOnlyMiddleware } = require('../middleware/auth');

// Todas las rutas de admin requieren token de administrador
router.use(adminOnlyMiddleware);

router.get('/tiendas',               getTiendas);              // GET  /api/admin/tiendas
router.patch('/tiendas/:id/estado',  actualizarEstadoTienda);  // PATCH /api/admin/tiendas/:id/estado

router.get('/usuarios',              getAdmins);               // GET  /api/admin/usuarios
router.post('/usuarios',             crearAdmin);              // POST /api/admin/usuarios
router.patch('/usuarios/:id/estado', actualizarEstadoAdmin);   // PATCH /api/admin/usuarios/:id/estado

router.get('/roles',                 getRoles);                // GET  /api/admin/roles
router.get('/pqrs',                  getPQRS);                 // GET  /api/admin/pqrs

module.exports = router;
