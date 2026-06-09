// src/controllers/authController.js
const { query } = require('../db');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../middleware/auth');

/**
 * POST /api/auth/admin/login
 * Login para administradores del panel web.
 * Body: { cCorreo: string, cPassword: string }
 * Response: { token: string, admin: {...} }
 */
async function loginAdmin(req, res) {
  try {
    const { cCorreo, cPassword } = req.body;

    if (!cCorreo || !cPassword) {
      return res.status(400).json({ success: false, message: 'Campos requeridos: cCorreo, cPassword.' });
    }

    const rows = await query(
      `SELECT nIdUsuario, cNombre, cApellido, cCorreo, cPassword, eEstado
       FROM TUsuarioAdmin WHERE cCorreo = ?`,
      [cCorreo]
    );

    if (rows.length === 0) {
      return res.status(401).json({ success: false, message: 'Credenciales inválidas.' });
    }

    const admin = rows[0];

    if (admin.eEstado !== 'Activo') {
      return res.status(403).json({
        success: false,
        message: `Cuenta ${admin.eEstado.toLowerCase()}. Contacta al superadministrador.`
      });
    }

    // NOTA: En los datos de prueba la contraseña es texto plano.
    // Para producción usa bcrypt.compare(). Este código soporta ambos.
    let passwordValido = false;
    if (admin.cPassword.startsWith('$2b$') || admin.cPassword.startsWith('$2a$')) {
      // Contraseña hasheada con bcrypt
      passwordValido = await bcrypt.compare(cPassword, admin.cPassword);
    } else {
      // Contraseña en texto plano (solo para desarrollo inicial)
      passwordValido = (cPassword === admin.cPassword);
    }

    if (!passwordValido) {
      return res.status(401).json({ success: false, message: 'Credenciales inválidas.' });
    }

    // Generar token JWT con expiración de 8 horas
    const token = jwt.sign(
      {
        id: admin.nIdUsuario,
        correo: admin.cCorreo,
        nombre: `${admin.cNombre} ${admin.cApellido}`,
        tipo: 'admin'   // <-- usado por adminOnlyMiddleware
      },
      JWT_SECRET,
      { expiresIn: '8h' }
    );

    return res.status(200).json({
      success: true,
      message: 'Login exitoso.',
      token,
      admin: {
        nIdUsuario: admin.nIdUsuario,
        cNombre: admin.cNombre,
        cApellido: admin.cApellido,
        cCorreo: admin.cCorreo
      }
    });

  } catch (error) {
    console.error('[loginAdmin] Error:', error);
    return res.status(500).json({ success: false, message: 'Error en el servidor.', error: error.message });
  }
}

/**
 * POST /api/auth/trabajador/login
 * Login para trabajadores de la app de escritorio.
 * Body: { cIdentificacion: string, cPassword: string, nTiendaFK: number }
 * Response: { token: string, trabajador: {...} }
 */
async function loginTrabajador(req, res) {
  try {
    const { cIdentificacion, cPassword, nTiendaFK } = req.body;

    if (!cIdentificacion || !cPassword || !nTiendaFK) {
      return res.status(400).json({
        success: false,
        message: 'Campos requeridos: cIdentificacion, cPassword, nTiendaFK.'
      });
    }

    // Busca el trabajador y verifica que pertenezca a la tienda indicada
    const rows = await query(
      `SELECT
        t.nTrabajadorID, t.cIdentificacion, t.cNombre, t.cApellido,
        t.cPassword, t.cTelefono,
        r.cNombre AS nombreRol, r.nRolID,
        tt.nTiendaFK
       FROM TTrabajador t
       INNER JOIN TRoles r ON t.nRolFK = r.nRolID
       INNER JOIN TTrabajadorTienda tt ON t.nTrabajadorID = tt.nTrabajadorFK
       WHERE t.cIdentificacion = ? AND tt.nTiendaFK = ?`,
      [cIdentificacion, nTiendaFK]
    );

    if (rows.length === 0) {
      return res.status(401).json({
        success: false,
        message: 'Trabajador no encontrado en esta tienda o credenciales inválidas.'
      });
    }

    const trabajador = rows[0];

    let passwordValido = false;
    if (trabajador.cPassword.startsWith('$2b$') || trabajador.cPassword.startsWith('$2a$')) {
      passwordValido = await bcrypt.compare(cPassword, trabajador.cPassword);
    } else {
      passwordValido = (cPassword === trabajador.cPassword);
    }

    if (!passwordValido) {
      return res.status(401).json({ success: false, message: 'Contraseña incorrecta.' });
    }

    const token = jwt.sign(
      {
        id: trabajador.nTrabajadorID,
        nombre: `${trabajador.cNombre} ${trabajador.cApellido}`,
        rol: trabajador.nombreRol,
        tiendaId: trabajador.nTiendaFK,
        tipo: 'trabajador'   // <-- usado por trabajadorOnlyMiddleware
      },
      JWT_SECRET,
      { expiresIn: '12h' }
    );

    return res.status(200).json({
      success: true,
      message: 'Login exitoso.',
      token,
      trabajador: {
        nTrabajadorID: trabajador.nTrabajadorID,
        cNombre: trabajador.cNombre,
        cApellido: trabajador.cApellido,
        cIdentificacion: trabajador.cIdentificacion,
        rol: trabajador.nombreRol,
        tiendaId: trabajador.nTiendaFK
      }
    });

  } catch (error) {
    console.error('[loginTrabajador] Error:', error);
    return res.status(500).json({ success: false, message: 'Error en el servidor.', error: error.message });
  }
}

module.exports = { loginAdmin, loginTrabajador };
