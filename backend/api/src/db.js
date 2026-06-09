// src/db.js - Configuración de conexión a MySQL con pool de conexiones
const mysql = require('mysql2/promise');

const pool = mysql.createPool({
  host:     process.env.DB_HOST     || '127.0.0.1',
  port:     parseInt(process.env.DB_PORT) || 8080,
  database: process.env.DB_NAME     || 'mercadoshop',
  user:     process.env.DB_USER     || 'root',
  password: process.env.DB_PASSWORD || '',
  waitForConnections: true,
  connectionLimit: 10,       // Máximo de conexiones simultáneas en el pool
  queueLimit: 0
});

// Función helper para ejecutar queries de forma segura
async function query(sql, params) {
  const [rows] = await pool.execute(sql, params);
  return rows;
}

module.exports = { pool, query };
