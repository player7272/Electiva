// src/controllers/productosController.js
const { query } = require('../db');

/**
 * GET /api/productos
 * Devuelve todos los productos activos (con stock > 0).
 * Query params opcionales: ?tienda=ID, ?categoria=ID, ?q=busqueda
 */
async function getProductos(req, res) {
  try {
    const { tienda, categoria, q } = req.query;

    let sql = `
      SELECT
        p.nProductoID,
        p.nTiendaFK,
        t.cNombreComercial   AS nombreTienda,
        p.cDescripcionCorta,
        p.cDescripcionLarga,
        p.cUrlImagenPrincipal,
        p.nCategoriaFK,
        c.cNombreCategoria,
        p.jEspecificaciones,
        p.nPrecioUnitario,
        p.nCantidadStock
      FROM TProductos p
      INNER JOIN TTiendas t ON p.nTiendaFK = t.nTiendaID
      LEFT JOIN TCategoria c ON p.nCategoriaFK = c.nCategoriaID
      WHERE t.eEstadoTienda = 'Activa'
        AND p.nCantidadStock > 0
    `;

    const params = [];

    if (tienda) {
      sql += ' AND p.nTiendaFK = ?';
      params.push(parseInt(tienda));
    }

    if (categoria) {
      sql += ' AND p.nCategoriaFK = ?';
      params.push(parseInt(categoria));
    }

    if (q) {
      sql += ' AND (p.cDescripcionCorta LIKE ? OR p.cDescripcionLarga LIKE ?)';
      params.push(`%${q}%`, `%${q}%`);
    }

    sql += ' ORDER BY p.nProductoID ASC';

    const productos = await query(sql, params);

    return res.status(200).json({
      success: true,
      total: productos.length,
      data: productos
    });

  } catch (error) {
    console.error('[getProductos] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener productos.', error: error.message });
  }
}

/**
 * GET /api/productos/:id
 * Devuelve un producto específico por ID.
 */
async function getProductoById(req, res) {
  try {
    const { id } = req.params;

    const rows = await query(`
      SELECT
        p.nProductoID,
        p.nTiendaFK,
        t.cNombreComercial AS nombreTienda,
        p.cDescripcionCorta,
        p.cDescripcionLarga,
        p.cUrlImagenPrincipal,
        p.nCategoriaFK,
        c.cNombreCategoria,
        p.jEspecificaciones,
        p.nPrecioUnitario,
        p.nCantidadStock
      FROM TProductos p
      INNER JOIN TTiendas t ON p.nTiendaFK = t.nTiendaID
      LEFT JOIN TCategoria c ON p.nCategoriaFK = c.nCategoriaID
      WHERE p.nProductoID = ?
    `, [id]);

    if (rows.length === 0) {
      return res.status(404).json({ success: false, message: `Producto con ID ${id} no encontrado.` });
    }

    return res.status(200).json({ success: true, data: rows[0] });

  } catch (error) {
    console.error('[getProductoById] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener producto.', error: error.message });
  }
}

/**
 * PUT /api/productos/:id/stock
 * Actualiza el stock de un producto. Usado por la app de escritorio.
 * Requiere token de trabajador.
 * Body: { nCantidadStock: number }
 */
async function actualizarStock(req, res) {
  try {
    const { id } = req.params;
    const { nCantidadStock } = req.body;

    if (nCantidadStock === undefined || nCantidadStock < 0) {
      return res.status(400).json({ success: false, message: 'nCantidadStock debe ser un número >= 0.' });
    }

    // Verifica que el producto pertenezca a la tienda del trabajador logueado
    const trabajadorTiendaFK = req.user.tiendaId;

    const productoRows = await query(
      'SELECT nTiendaFK FROM TProductos WHERE nProductoID = ?',
      [id]
    );

    if (productoRows.length === 0) {
      return res.status(404).json({ success: false, message: 'Producto no encontrado.' });
    }

    if (productoRows[0].nTiendaFK !== trabajadorTiendaFK) {
      return res.status(403).json({ success: false, message: 'No tienes permisos para editar productos de otra tienda.' });
    }

    await query(
      'UPDATE TProductos SET nCantidadStock = ? WHERE nProductoID = ?',
      [nCantidadStock, id]
    );

    return res.status(200).json({
      success: true,
      message: `Stock del producto ${id} actualizado a ${nCantidadStock} unidades.`
    });

  } catch (error) {
    console.error('[actualizarStock] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al actualizar stock.', error: error.message });
  }
}

/**
 * POST /api/productos
 * Crea un nuevo producto. Usado por la app de escritorio (trabajador con rol Administrador/Bodeguero).
 * Body: { nTiendaFK, cDescripcionCorta, cDescripcionLarga, cUrlImagenPrincipal, nCategoriaFK, nPrecioUnitario, nCantidadStock, jEspecificaciones? }
 */
async function crearProducto(req, res) {
  try {
    const {
      nTiendaFK,
      cDescripcionCorta,
      cDescripcionLarga,
      cUrlImagenPrincipal,
      nCategoriaFK,
      nPrecioUnitario,
      nCantidadStock,
      jEspecificaciones
    } = req.body;

    if (!nTiendaFK || !cDescripcionCorta || !nPrecioUnitario || nCantidadStock === undefined) {
      return res.status(400).json({
        success: false,
        message: 'Campos requeridos: nTiendaFK, cDescripcionCorta, nPrecioUnitario, nCantidadStock'
      });
    }

    const result = await query(
      `INSERT INTO TProductos (nTiendaFK, cDescripcionCorta, cDescripcionLarga, cUrlImagenPrincipal,
        nCategoriaFK, jEspecificaciones, nPrecioUnitario, nCantidadStock)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        nTiendaFK,
        cDescripcionCorta,
        cDescripcionLarga || null,
        cUrlImagenPrincipal || null,
        nCategoriaFK || null,
        jEspecificaciones ? JSON.stringify(jEspecificaciones) : null,
        nPrecioUnitario,
        nCantidadStock
      ]
    );

    return res.status(201).json({
      success: true,
      message: 'Producto creado exitosamente.',
      nProductoID: result.insertId
    });

  } catch (error) {
    console.error('[crearProducto] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al crear producto.', error: error.message });
  }
}

module.exports = { getProductos, getProductoById, actualizarStock, crearProducto };
