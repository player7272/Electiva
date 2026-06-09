// src/routes/auth.js
const express = require('express');
const router = express.Router();
const { loginAdmin, loginTrabajador } = require('../controllers/authController');

// POST /api/auth/admin/login     - Login del panel web
router.post('/admin/login',      loginAdmin);

// POST /api/auth/trabajador/login - Login de la app de escritorio
router.post('/trabajador/login', loginTrabajador);

module.exports = router;
