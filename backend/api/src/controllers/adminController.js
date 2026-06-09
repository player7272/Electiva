// src/controllers/adminController.js
const { query } = require('../db');
const bcrypt = require('bcryptjs');

/**
 * GET /api/admin/tiendas
 * Lista todas las tiendas con su estado de membresía.
 */
async function getTiendas(req, res) {
  try {
    const tiendas = await query(`
      SELECT
        nTiendaID,
        cNombreComercial,
        cRazonSocial,
        cCorreoAtencion,
        cTelefonoAtencion,
        eEstadoTienda,
        nPlanFK,
        dFechaVencimientoSuscripcion
      FROM TTiendas
      ORDER BY nTiendaID ASC
    `);

    return res.status(200).json({ success: true, total: tiendas.length, data: tiendas });
  } catch (error) {
    console.error('[getTiendas] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener tiendas.' });
  }
}

/**
 * PATCH /api/admin/tiendas/:id/estado
 * Activa, suspende o desactiva la membresía de una tienda.
 * Body: { eEstadoTienda: 'Activa' | 'Inactiva' | 'Suspendida' | 'Pendiente' }
 */
async function actualizarEstadoTienda(req, res) {
  try {
    const { id } = req.params;
    const { eEstadoTienda } = req.body;

    const estadosValidos = ['Activa', 'Inactiva', 'Suspendida', 'Pendiente'];
    if (!estadosValidos.includes(eEstadoTienda)) {
      return res.status(400).json({
        success: false,
        message: `eEstadoTienda debe ser uno de: ${estadosValidos.join(', ')}`
      });
    }

    await query('UPDATE TTiendas SET eEstadoTienda = ? WHERE nTiendaID = ?', [eEstadoTienda, id]);

    return res.status(200).json({
      success: true,
      message: `Estado de tienda ${id} actualizado a: ${eEstadoTienda}`
    });
  } catch (error) {
    console.error('[actualizarEstadoTienda] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al actualizar estado de tienda.' });
  }
}

/**
 * GET /api/admin/usuarios
 * Lista todos los administradores del sistema.
 */
async function getAdmins(req, res) {
  try {
    const admins = await query(`
      SELECT nIdUsuario, cNombre, cApellido, cCorreo, eEstado, dCreacion
      FROM TUsuarioAdmin
      ORDER BY nIdUsuario ASC
    `);

    return res.status(200).json({ success: true, total: admins.length, data: admins });
  } catch (error) {
    console.error('[getAdmins] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener administradores.' });
  }
}

/**
 * POST /api/admin/usuarios
 * Crea un nuevo usuario administrador.
 * Body: { cNombre, cApellido, cCorreo, cPassword }
 */
async function crearAdmin(req, res) {
  try {
    const { cNombre, cApellido, cCorreo, cPassword } = req.body;

    if (!cNombre || !cApellido || !cCorreo || !cPassword) {
      return res.status(400).json({
        success: false,
        message: 'Campos requeridos: cNombre, cApellido, cCorreo, cPassword.'
      });
    }

    const existente = await query('SELECT nIdUsuario FROM TUsuarioAdmin WHERE cCorreo = ?', [cCorreo]);
    if (existente.length > 0) {
      return res.status(409).json({ success: false, message: 'Ya existe un administrador con ese correo.' });
    }

    const passwordHash = await bcrypt.hash(cPassword, 10);

    const result = await query(
      `INSERT INTO TUsuarioAdmin (cNombre, cApellido, cCorreo, cPassword, eEstado)
       VALUES (?, ?, ?, ?, 'Activo')`,
      [cNombre, cApellido, cCorreo, passwordHash]
    );

    return res.status(201).json({
      success: true,
      message: 'Administrador creado exitosamente.',
      nIdUsuario: result.insertId
    });
  } catch (error) {
    console.error('[crearAdmin] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al crear administrador.' });
  }
}

/**
 * PATCH /api/admin/usuarios/:id/estado
 * Activa, desactiva o bloquea un usuario administrador.
 * Body: { eEstado: 'Activo' | 'Inactivo' | 'Bloqueado' }
 */
async function actualizarEstadoAdmin(req, res) {
  try {
    const { id } = req.params;
    const { eEstado } = req.body;

    const estadosValidos = ['Activo', 'Inactivo', 'Bloqueado'];
    if (!estadosValidos.includes(eEstado)) {
      return res.status(400).json({
        success: false,
        message: `eEstado debe ser uno de: ${estadosValidos.join(', ')}`
      });
    }

    await query('UPDATE TUsuarioAdmin SET eEstado = ? WHERE nIdUsuario = ?', [eEstado, id]);

    return res.status(200).json({
      success: true,
      message: `Estado del admin ${id} actualizado a: ${eEstado}`
    });
  } catch (error) {
    console.error('[actualizarEstadoAdmin] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al actualizar estado del admin.' });
  }
}

/**
 * GET /api/admin/roles
 * Lista todos los roles disponibles en el sistema.
 */
async function getRoles(req, res) {
  try {
    const roles = await query('SELECT nRolID, cNombre, cDescripcion FROM TRoles ORDER BY nRolID ASC');
    return res.status(200).json({ success: true, data: roles });
  } catch (error) {
    console.error('[getRoles] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener roles.' });
  }
}

/**
 * GET /api/admin/pqrs
 * Lista todas las PQRS del sistema con paginación.
 */
async function getPQRS(req, res) {
  try {
    const { estado, tipo } = req.query;

    let sql = `
      SELECT
        p.nPQRSID,
        p.cNumeroTicket,
        p.cAsunto,
        p.eTipo,
        p.eEstado,
        p.cTipoCreador,
        p.dFechaCreacion,
        pe.cNumeroComprobante AS pedidoComprobante
      FROM TPQRS p
      LEFT JOIN TPedido pe ON p.nPedidoFK = pe.nPedidoID
    `;

    const params = [];
    const condiciones = [];

    if (estado) { condiciones.push('p.eEstado = ?'); params.push(estado); }
    if (tipo) { condiciones.push('p.eTipo = ?'); params.push(tipo); }

    if (condiciones.length > 0) sql += ' WHERE ' + condiciones.join(' AND ');
    sql += ' ORDER BY p.dFechaCreacion DESC LIMIT 200';

    const pqrs = await query(sql, params);

    return res.status(200).json({ success: true, total: pqrs.length, data: pqrs });
  } catch (error) {
    console.error('[getPQRS] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener PQRS.' });
  }
}

module.exports = {
  getTiendas,
  actualizarEstadoTienda,
  getAdmins,
  crearAdmin,
  actualizarEstadoAdmin,
  getRoles,
  getPQRS
};
