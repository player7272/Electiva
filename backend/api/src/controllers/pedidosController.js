// src/controllers/pedidosController.js
const { query, pool } = require('../db');

/**
 * POST /api/pedidos
 * Registra un pedido completo con sus detalles.
 * Usado por la app móvil Android (canal del comprador).
 *
 * Body esperado:
 * {
 *   "cliente": {
 *     "cNombre": "Juan",
 *     "cApellido": "García",
 *     "cDocumento": "1234567890",
 *     "cCorreo": "juan@email.com",
 *     "cTelefono": "3001234567"
 *   },
 *   "direccionEnvio": {
 *     "cNomenclatura": "Calle 10 # 20-30",
 *     "cBarrio": "El Poblado",
 *     "cNotasAdicionales": "Apto 301",
 *     "cCodigoPostal": "050010",
 *     "nMunicipioFK": 1,
 *     "cNombreRecibidor": "Juan García",
 *     "cTelefonoRecibidor": "3001234567"
 *   },
 *   "items": [
 *     { "nProductoID": 1, "nCantidad": 2 },
 *     { "nProductoID": 3, "nCantidad": 1 }
 *   ],
 *   "nCostoEnvio": 8000
 * }
 */
async function crearPedido(req, res) {
  const connection = await pool.getConnection();

  try {
    await connection.beginTransaction();

    const { cliente, direccionEnvio, items, nCostoEnvio } = req.body;

    // --- Validaciones de entrada ---
    if (!cliente || !direccionEnvio || !items || items.length === 0) {
      return res.status(400).json({
        success: false,
        message: 'Campos requeridos: cliente, direccionEnvio, items (array con al menos 1 producto).'
      });
    }

    // --- PASO 1: Crear o reutilizar el cliente ---
    let nClienteID;
    const [clienteExistente] = await connection.execute(
      'SELECT nUsuarioClienteID FROM TUsuarioCliente WHERE cDocumento = ? OR cCorreo = ? LIMIT 1',
      [cliente.cDocumento, cliente.cCorreo]
    );

    if (clienteExistente.length > 0) {
      nClienteID = clienteExistente[0].nUsuarioClienteID;
    } else {
      // Primero crear una dirección base para el cliente
      const [dirResult] = await connection.execute(
        `INSERT INTO TDireccion (cNomenclatura, cBarrio, cNotasAdicionales, cCodigoPostal, nMunicipioFK)
         VALUES (?, ?, ?, ?, ?)`,
        [
          direccionEnvio.cNomenclatura,
          direccionEnvio.cBarrio,
          direccionEnvio.cNotasAdicionales || null,
          direccionEnvio.cCodigoPostal || null,
          direccionEnvio.nMunicipioFK
        ]
      );
      const nDireccionID = dirResult.insertId;

      const [clienteResult] = await connection.execute(
        `INSERT INTO TUsuarioCliente (cNombre, cApellido, cDocumento, cContrasena, cCorreo, cTelefono, nDireccionFK)
         VALUES (?, ?, ?, ?, ?, ?, ?)`,
        [
          cliente.cNombre,
          cliente.cApellido,
          cliente.cDocumento,
          'temp_pass_' + Date.now(),  // Contraseña temporal - el cliente puede cambiarla después
          cliente.cCorreo,
          cliente.cTelefono,
          nDireccionID
        ]
      );
      nClienteID = clienteResult.insertId;
    }

    // --- PASO 2: Crear dirección de envío del pedido ---
    const [dirEnvioResult] = await connection.execute(
      `INSERT INTO TDireccion (cNomenclatura, cBarrio, cNotasAdicionales, cCodigoPostal, nMunicipioFK)
       VALUES (?, ?, ?, ?, ?)`,
      [
        direccionEnvio.cNomenclatura,
        direccionEnvio.cBarrio,
        direccionEnvio.cNotasAdicionales || null,
        direccionEnvio.cCodigoPostal || null,
        direccionEnvio.nMunicipioFK
      ]
    );

    const [dirClienteResult] = await connection.execute(
      `INSERT INTO TDireccionCliente (nClienteFK, nDireccionFK, cEtiqueta, cNombreRecibidor, cTelefonoRecibidor)
       VALUES (?, ?, ?, ?, ?)`,
      [
        nClienteID,
        dirEnvioResult.insertId,
        'Pedido',
        direccionEnvio.cNombreRecibidor || `${cliente.cNombre} ${cliente.cApellido}`,
        direccionEnvio.cTelefonoRecibidor || cliente.cTelefono
      ]
    );
    const nDireccionClienteID = dirClienteResult.insertId;

    // --- PASO 3: Validar stock y calcular subtotal ---
    let nSubtotal = 0;
    const detallesValidos = [];

    for (const item of items) {
      const [productoRows] = await connection.execute(
        'SELECT nProductoID, cDescripcionCorta, nPrecioUnitario, nCantidadStock FROM TProductos WHERE nProductoID = ?',
        [item.nProductoID]
      );

      if (productoRows.length === 0) {
        await connection.rollback();
        return res.status(400).json({
          success: false,
          message: `Producto con ID ${item.nProductoID} no existe.`
        });
      }

      const producto = productoRows[0];

      if (producto.nCantidadStock < item.nCantidad) {
        await connection.rollback();
        return res.status(400).json({
          success: false,
          message: `Stock insuficiente para "${producto.cDescripcionCorta}". Disponible: ${producto.nCantidadStock}, solicitado: ${item.nCantidad}.`
        });
      }

      const subtotalItem = parseFloat(producto.nPrecioUnitario) * item.nCantidad;
      nSubtotal += subtotalItem;

      detallesValidos.push({
        nProductoID: producto.nProductoID,
        cNombreProducto: producto.cDescripcionCorta,
        nPrecioCompra: producto.nPrecioUnitario,
        nCantidad: item.nCantidad,
        nSubtotal: subtotalItem
      });
    }

    const costoEnvio = parseFloat(nCostoEnvio || 0);
    const nTotal = nSubtotal + costoEnvio;

    // Generar número de comprobante único
    const cNumeroComprobante = `PED-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    // --- PASO 4: Crear el pedido (estado inicial = 1 = Pendiente) ---
    const [pedidoResult] = await connection.execute(
      `INSERT INTO TPedido (nClienteFK, nDireccionClienteFK, cNumeroComprobante,
        nSubtotal, nCostoEnvio, nTotal, nEstadoPedidoFK)
       VALUES (?, ?, ?, ?, ?, ?, 1)`,
      [nClienteID, nDireccionClienteID, cNumeroComprobante, nSubtotal, costoEnvio, nTotal]
    );
    const nPedidoID = pedidoResult.insertId;

    // --- PASO 5: Insertar detalles del pedido y descontar stock ---
    for (const detalle of detallesValidos) {
      await connection.execute(
        `INSERT INTO TDetallePedido (nPedidoFK, nProductoFK, cNombreProducto, nPrecioCompra, nCantidad, nSubtotal)
         VALUES (?, ?, ?, ?, ?, ?)`,
        [
          nPedidoID,
          detalle.nProductoID,
          detalle.cNombreProducto,
          detalle.nPrecioCompra,
          detalle.nCantidad,
          detalle.nSubtotal
        ]
      );

      // Descontar stock del producto
      await connection.execute(
        'UPDATE TProductos SET nCantidadStock = nCantidadStock - ? WHERE nProductoID = ?',
        [detalle.nCantidad, detalle.nProductoID]
      );
    }

    await connection.commit();

    return res.status(201).json({
      success: true,
      message: 'Pedido registrado exitosamente.',
      data: {
        nPedidoID,
        cNumeroComprobante,
        nSubtotal,
        nCostoEnvio: costoEnvio,
        nTotal,
        estadoPedido: 'Pendiente',
        detalles: detallesValidos
      }
    });

  } catch (error) {
    await connection.rollback();
    console.error('[crearPedido] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al crear pedido.', error: error.message });
  } finally {
    connection.release();
  }
}

/**
 * GET /api/pedidos
 * Lista todos los pedidos. Usado por la app de escritorio para validar comprobantes.
 * Query params: ?comprobante=PED-xxx (buscar por número de comprobante)
 */
async function getPedidos(req, res) {
  try {
    const { comprobante } = req.query;

    let sql = `
      SELECT
        p.nPedidoID,
        p.cNumeroComprobante,
        CONCAT(c.cNombre, ' ', c.cApellido) AS nombreCliente,
        c.cTelefono,
        p.nSubtotal,
        p.nCostoEnvio,
        p.nTotal,
        ep.cNombreEstado AS estadoPedido,
        p.dFechaActualizacion
      FROM TPedido p
      INNER JOIN TUsuarioCliente c ON p.nClienteFK = c.nUsuarioClienteID
      INNER JOIN TEstadoPedido ep ON p.nEstadoPedidoFK = ep.nEstadoPedidoID
    `;

    const params = [];

    if (comprobante) {
      sql += ' WHERE p.cNumeroComprobante = ?';
      params.push(comprobante);
    }

    sql += ' ORDER BY p.nPedidoID DESC LIMIT 100';

    const pedidos = await query(sql, params);

    return res.status(200).json({ success: true, total: pedidos.length, data: pedidos });

  } catch (error) {
    console.error('[getPedidos] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al obtener pedidos.', error: error.message });
  }
}

/**
 * PATCH /api/pedidos/:id/estado
 * Actualiza el estado de un pedido. Usado por app de escritorio.
 * Body: { nEstadoPedidoFK: number }
 */
async function actualizarEstadoPedido(req, res) {
  try {
    const { id } = req.params;
    const { nEstadoPedidoFK } = req.body;

    if (!nEstadoPedidoFK) {
      return res.status(400).json({ success: false, message: 'Campo requerido: nEstadoPedidoFK (1-6).' });
    }

    const estadoRows = await query(
      'SELECT cNombreEstado FROM TEstadoPedido WHERE nEstadoPedidoID = ?',
      [nEstadoPedidoFK]
    );

    if (estadoRows.length === 0) {
      return res.status(400).json({ success: false, message: 'Estado de pedido inválido.' });
    }

    await query(
      'UPDATE TPedido SET nEstadoPedidoFK = ? WHERE nPedidoID = ?',
      [nEstadoPedidoFK, id]
    );

    return res.status(200).json({
      success: true,
      message: `Pedido ${id} actualizado a estado: ${estadoRows[0].cNombreEstado}`
    });

  } catch (error) {
    console.error('[actualizarEstadoPedido] Error:', error);
    return res.status(500).json({ success: false, message: 'Error al actualizar estado.', error: error.message });
  }
}

module.exports = { crearPedido, getPedidos, actualizarEstadoPedido };
