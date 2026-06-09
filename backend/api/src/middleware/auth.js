// src/middleware/auth.js - Middleware de autenticación JWT
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'jwt_secreto_muy_seguro_cambiar_en_produccion';

/**
 * Middleware que verifica el token JWT en el header Authorization.
 * Uso: router.get('/ruta-protegida', authMiddleware, controller)
 */
function authMiddleware(req, res, next) {
  const authHeader = req.headers['authorization'];

  if (!authHeader) {
    return res.status(401).json({
      success: false,
      message: 'Token de autorización requerido. Header: Authorization: Bearer <token>'
    });
  }

  // El header debe tener el formato: "Bearer <token>"
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return res.status(401).json({
      success: false,
      message: 'Formato de token inválido. Use: Bearer <token>'
    });
  }

  const token = parts[1];

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;  // Adjunta el payload del token al request
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ success: false, message: 'Token expirado. Inicie sesión de nuevo.' });
    }
    return res.status(401).json({ success: false, message: 'Token inválido.' });
  }
}

/**
 * Middleware solo para administradores del panel web.
 * Verifica que el token sea de tipo 'admin'.
 */
function adminOnlyMiddleware(req, res, next) {
  authMiddleware(req, res, () => {
    if (req.user.tipo !== 'admin') {
      return res.status(403).json({ success: false, message: 'Acceso denegado. Se requiere rol de administrador.' });
    }
    next();
  });
}

/**
 * Middleware solo para trabajadores de tienda (app de escritorio).
 * Verifica que el token sea de tipo 'trabajador'.
 */
function trabajadorOnlyMiddleware(req, res, next) {
  authMiddleware(req, res, () => {
    if (req.user.tipo !== 'trabajador') {
      return res.status(403).json({ success: false, message: 'Acceso denegado. Solo para trabajadores.' });
    }
    next();
  });
}

module.exports = { authMiddleware, adminOnlyMiddleware, trabajadorOnlyMiddleware, JWT_SECRET };
