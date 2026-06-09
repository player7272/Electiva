// src/server.js - Punto de entrada principal del servidor
require('dotenv').config();

const express = require('express');
const cors    = require('cors');

const productosRouter = require('./routes/productos');
const pedidosRouter   = require('./routes/pedidos');
const authRouter      = require('./routes/auth');
const adminRouter     = require('./routes/admin');

const app  = express();
const PORT = process.env.PORT || 8080;

// ============================================================
// MIDDLEWARES GLOBALES
// ============================================================
app.use(cors({
  origin: '*',   // En producción, restringe a los dominios de tus apps
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ============================================================
// RUTA DE SALUD (para verificar que el servidor está vivo)
// ============================================================
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    endpoints: {
      auth:     '/api/auth/admin/login | /api/auth/trabajador/login',
      productos: '/api/productos',
      pedidos:   '/api/pedidos',
      admin:     '/api/admin/tiendas | /api/admin/usuarios | /api/admin/roles | /api/admin/pqrs'
    }
  });
});

// ============================================================
// RUTAS PRINCIPALES
// ============================================================
app.use('/api/auth',      authRouter);
app.use('/api/productos', productosRouter);
app.use('/api/pedidos',   pedidosRouter);
app.use('/api/admin',     adminRouter);

// ============================================================
// MANEJADOR DE ERRORES GLOBAL
// ============================================================
app.use((err, req, res, next) => {
  console.error('[ERROR GLOBAL]', err.stack);
  res.status(500).json({
    success: false,
    message: 'Error interno del servidor.',
    error: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// ============================================================
// INICIO DEL SERVIDOR
// ============================================================
app.listen(PORT, '0.0.0.0', () => {
  console.log(`\n╔══════════════════════════════════════╗`);
  console.log(`║  API Ecosistema corriendo en :${PORT}  ║`);
  console.log(`╚══════════════════════════════════════╝`);
  console.log(`\n  Health check: http://localhost:${PORT}/health`);
  console.log(`  DB Host:      ${process.env.DB_HOST || '127.0.0.1'}:${process.env.DB_PORT || 8080}`);
  console.log(`  DB Name:      ${process.env.DB_NAME || 'mercadoshop'}\n`);
});

module.exports = app;
