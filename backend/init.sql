-- ======================================================
-- SCRIPT COMPLETO DE INICIALIZACIÓN DE BASE DE DATOS
-- ======================================================
SET FOREIGN_KEY_CHECKS = 0;

-- ======================================================
-- 1. TABLAS INDEPENDIENTES Y COMPARTIDAS
-- ======================================================

CREATE TABLE IF NOT EXISTS TDepartamento (
  nDepartamentoID INT PRIMARY KEY AUTO_INCREMENT,
  cNombre VARCHAR(255),
  cCodigoDane VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TMunicipio (
  nMunicipioID INT PRIMARY KEY AUTO_INCREMENT,
  nDepartamentoFK INT,
  cNombre VARCHAR(255),
  cCodigoDane VARCHAR(255),
  FOREIGN KEY (nDepartamentoFK) REFERENCES TDepartamento(nDepartamentoID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TDireccion (
  nDireccionID INT PRIMARY KEY AUTO_INCREMENT,
  cNomenclatura VARCHAR(255),
  cBarrio VARCHAR(255),
  cNotasAdicionales VARCHAR(255),
  cCodigoPostal VARCHAR(255),
  nMunicipioFK INT,
  FOREIGN KEY (nMunicipioFK) REFERENCES TMunicipio(nMunicipioID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TEstadoPedido (
  nEstadoPedidoID INT PRIMARY KEY AUTO_INCREMENT,
  cNombreEstado VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TRoles (
  nRolID INT PRIMARY KEY AUTO_INCREMENT,
  cNombre VARCHAR(255),
  cDescripcion VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TCategoria (
  nCategoriaID INT PRIMARY KEY AUTO_INCREMENT,
  cNombreCategoria VARCHAR(255),
  nCategoriaPadreFK INT,
  bEstado BOOLEAN,
  FOREIGN KEY (nCategoriaPadreFK) REFERENCES TCategoria(nCategoriaID)
) ENGINE=InnoDB;

-- ======================================================
-- 2. MÓDULO CLIENTE
-- ======================================================

CREATE TABLE IF NOT EXISTS TUsuarioCliente (
  nUsuarioClienteID INT PRIMARY KEY AUTO_INCREMENT,
  cNombre VARCHAR(255),
  cApellido VARCHAR(255),
  cDocumento VARCHAR(255),
  cContrasena VARCHAR(255),
  cCorreo VARCHAR(255),
  cTelefono VARCHAR(255),
  nDireccionFK INT,
  FOREIGN KEY (nDireccionFK) REFERENCES TDireccion(nDireccionID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TDireccionCliente (
  nDireccionClienteID INT PRIMARY KEY AUTO_INCREMENT,
  nClienteFK INT,
  nDireccionFK INT,
  cEtiqueta VARCHAR(255),
  cNombreRecibidor VARCHAR(255),
  cTelefonoRecibidor VARCHAR(255),
  FOREIGN KEY (nClienteFK) REFERENCES TUsuarioCliente(nUsuarioClienteID),
  FOREIGN KEY (nDireccionFK) REFERENCES TDireccion(nDireccionID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TCarrito (
  nCarritoID INT PRIMARY KEY AUTO_INCREMENT,
  nUsuarioClienteFK INT,
  eEstado VARCHAR(255),
  dFechaUltActualizacion TIMESTAMP,
  dFechaExpiracion TIMESTAMP,
  FOREIGN KEY (nUsuarioClienteFK) REFERENCES TUsuarioCliente(nUsuarioClienteID)
) ENGINE=InnoDB;

-- ======================================================
-- 3. MÓDULO TIENDA
-- ======================================================

CREATE TABLE IF NOT EXISTS TTiendas (
  nTiendaID INT PRIMARY KEY AUTO_INCREMENT,
  cNombreComercial VARCHAR(255),
  tDescripcion TEXT,
  cUrlLogo VARCHAR(255),
  cCorreoAtencion VARCHAR(255),
  cTelefonoAtencion VARCHAR(255),
  cRazonSocial VARCHAR(255),
  nDireccionFK INT,
  cCodigoPostal VARCHAR(255),
  eEstadoTienda ENUM('Activa', 'Inactiva', 'Suspendida', 'Pendiente') DEFAULT 'Pendiente',
  nPlanFK INT,
  dFechaVencimientoSuscripcion TIMESTAMP,
  FOREIGN KEY (nDireccionFK) REFERENCES TDireccion(nDireccionID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TProductos (
  nProductoID INT PRIMARY KEY AUTO_INCREMENT,
  nTiendaFK INT,
  cDescripcionCorta VARCHAR(255),
  cDescripcionLarga TEXT,
  cUrlImagenPrincipal VARCHAR(255),
  nCategoriaFK INT,
  jEspecificaciones JSON,
  nPrecioUnitario DECIMAL(19,4),
  nCantidadStock INT,
  FOREIGN KEY (nTiendaFK) REFERENCES TTiendas(nTiendaID),
  FOREIGN KEY (nCategoriaFK) REFERENCES TCategoria(nCategoriaID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TTrabajador (
  nTrabajadorID INT PRIMARY KEY AUTO_INCREMENT,
  cIdentificacion VARCHAR(255),
  cNombre VARCHAR(255),
  cApellido VARCHAR(255),
  cPassword VARCHAR(255),
  cTelefono VARCHAR(255),
  nRolFK INT,
  FOREIGN KEY (nRolFK) REFERENCES TRoles(nRolID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TTrabajadorTienda (
  nID INT PRIMARY KEY AUTO_INCREMENT,
  nTiendaFK INT,
  nTrabajadorFK INT,
  FOREIGN KEY (nTiendaFK) REFERENCES TTiendas(nTiendaID),
  FOREIGN KEY (nTrabajadorFK) REFERENCES TTrabajador(nTrabajadorID)
) ENGINE=InnoDB;

-- ======================================================
-- 4. PEDIDOS Y TRANSACCIONES
-- ======================================================

CREATE TABLE IF NOT EXISTS TPedido (
  nPedidoID INT PRIMARY KEY AUTO_INCREMENT,
  nClienteFK INT,
  nDireccionClienteFK INT,
  cNumeroComprobante VARCHAR(255),
  nSubtotal DECIMAL(19,4),
  nCostoEnvio DECIMAL(19,4),
  nTotal DECIMAL(19,4),
  nTransaccionPasarelaFK INT,
  nEstadoPedidoFK INT,
  dFechaActualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (nClienteFK) REFERENCES TUsuarioCliente(nUsuarioClienteID),
  FOREIGN KEY (nDireccionClienteFK) REFERENCES TDireccionCliente(nDireccionClienteID),
  FOREIGN KEY (nEstadoPedidoFK) REFERENCES TEstadoPedido(nEstadoPedidoID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TDetallePedido (
  nDetallePedidoID INT PRIMARY KEY AUTO_INCREMENT,
  nPedidoFK INT,
  nProductoFK INT,
  cNombreProducto VARCHAR(255),
  nPrecioCompra DECIMAL(19,4),
  nCantidad INT,
  nSubtotal DECIMAL(19,4),
  FOREIGN KEY (nPedidoFK) REFERENCES TPedido(nPedidoID),
  FOREIGN KEY (nProductoFK) REFERENCES TProductos(nProductoID)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TTransaccionPasarela (
  nTransaccionID INT PRIMARY KEY AUTO_INCREMENT,
  nPedidoFK INT,
  cNombrePasarela VARCHAR(255),
  cIdTransaccionExterna VARCHAR(255),
  cMetodoPago VARCHAR(255),
  eFranquicia ENUM('Visa', 'Mastercard', 'AMEX'),
  cUltimos4Digitos VARCHAR(4),
  nCuotas INT,
  nValorTransaccion DECIMAL(19,4),
  cEstadoTransaccion VARCHAR(255),
  cCodigoAprobacionBanco VARCHAR(255),
  dFechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  dFechaActualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  jRawResponse JSON,
  FOREIGN KEY (nPedidoFK) REFERENCES TPedido(nPedidoID)
) ENGINE=InnoDB;

-- ======================================================
-- 5. MÓDULO ADMIN Y PQRS
-- ======================================================

CREATE TABLE IF NOT EXISTS TUsuarioAdmin (
  nIdUsuario INT PRIMARY KEY AUTO_INCREMENT,
  cNombre VARCHAR(255),
  cApellido VARCHAR(255),
  cCorreo VARCHAR(255),
  cPassword VARCHAR(255),
  eEstado ENUM('Activo', 'Inactivo', 'Bloqueado') DEFAULT 'Activo',
  dCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TTiendaAdmin (
  nIdTienda INT PRIMARY KEY AUTO_INCREMENT,
  cNombre VARCHAR(255),
  cDireccion VARCHAR(255),
  cTelefono VARCHAR(255),
  eEstado ENUM('Activa', 'Inactiva', 'Suspendida', 'Pendiente') DEFAULT 'Pendiente'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS TPQRS (
  nPQRSID INT PRIMARY KEY AUTO_INCREMENT,
  nCreadorFK INT,
  cTipoCreador ENUM('Usuario', 'Tienda', 'Admin'),
  dFechaCreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  eTipo ENUM('Peticion', 'Queja', 'Reclamo', 'Sugerencia'),
  eEstado ENUM('Activo', 'Resuelto', 'Pendiente') DEFAULT 'Activo',
  cNumeroTicket VARCHAR(255),
  cAsunto VARCHAR(255),
  nPedidoFK INT,
  nTiendaFK INT,
  FOREIGN KEY (nPedidoFK) REFERENCES TPedido(nPedidoID),
  FOREIGN KEY (nTiendaFK) REFERENCES TTiendaAdmin(nIdTienda)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS THiloPQRS (
  nHiloPQRSID INT PRIMARY KEY AUTO_INCREMENT,
  nPQRSFK INT,
  cMensaje TEXT,
  dFechaEnvio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  nActorFK INT,
  cTipoActor ENUM('Usuario', 'Tienda', 'Admin'),
  bEsMensajeInterno BOOLEAN DEFAULT FALSE,
  cEvidencia VARCHAR(255),
  FOREIGN KEY (nPQRSFK) REFERENCES TPQRS(nPQRSID)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- ======================================================
-- 6. DATOS DE PRUEBA INICIALES
-- ======================================================

INSERT INTO TEstadoPedido (cNombreEstado) VALUES
  ('Pendiente'), ('Confirmado'), ('En Preparacion'), ('En Camino'), ('Entregado'), ('Cancelado');

INSERT INTO TRoles (cNombre, cDescripcion) VALUES
  ('Administrador', 'Control total de la tienda'),
  ('Vendedor', 'Puede registrar ventas y gestionar inventario'),
  ('Bodeguero', 'Solo puede actualizar stock');

INSERT INTO TDepartamento (cNombre, cCodigoDane) VALUES
  ('Antioquia', '05'),
  ('Cundinamarca', '25');

INSERT INTO TMunicipio (nDepartamentoFK, cNombre, cCodigoDane) VALUES
  (1, 'Medellín', '05001'),
  (1, 'Bello', '05088'),
  (2, 'Bogotá D.C.', '25001');

INSERT INTO TCategoria (cNombreCategoria, nCategoriaPadreFK, bEstado) VALUES
  ('Electrónica', NULL, TRUE),
  ('Ropa', NULL, TRUE),
  ('Hogar', NULL, TRUE),
  ('Smartphones', 1, TRUE),
  ('Camisas', 2, TRUE);

INSERT INTO TDireccion (cNomenclatura, cBarrio, cNotasAdicionales, cCodigoPostal, nMunicipioFK) VALUES
  ('Calle 10 # 20-30', 'El Poblado', 'Local 1', '050010', 1);

INSERT INTO TTiendas (cNombreComercial, tDescripcion, cCorreoAtencion, cTelefonoAtencion,
  cRazonSocial, nDireccionFK, eEstadoTienda, nPlanFK, dFechaVencimientoSuscripcion)
VALUES
  ('TechStore Medellín', 'Tienda de tecnología y gadgets', 'contacto@techstore.co',
   '3001234567', 'TechStore SAS', 1, 'Activa', 1, '2026-12-31 00:00:00');

INSERT INTO TProductos (nTiendaFK, cDescripcionCorta, cDescripcionLarga, cUrlImagenPrincipal,
  nCategoriaFK, nPrecioUnitario, nCantidadStock)
VALUES
  (1, 'Smartphone XPro 12', 'Smartphone con pantalla AMOLED 6.7 pulgadas, 256GB, cámara 108MP',
   'https://via.placeholder.com/300x300?text=XPro12', 4, 1299900.00, 25),
  (1, 'Auriculares BT Pro', 'Auriculares bluetooth con cancelación de ruido, 30h batería',
   'https://via.placeholder.com/300x300?text=BTPro', 1, 299900.00, 50),
  (1, 'Cargador Rápido 65W', 'Cargador GaN 65W compatible con USB-C y USB-A',
   'https://via.placeholder.com/300x300?text=Cargador65W', 1, 89900.00, 100),
  (1, 'Funda Silicona Premium', 'Funda de silicona líquida para smartphones, varios colores',
   'https://via.placeholder.com/300x300?text=FundaPremium', 1, 39900.00, 200);

INSERT INTO TUsuarioAdmin (cNombre, cApellido, cCorreo, cPassword, eEstado)
VALUES ('Super', 'Admin', 'admin@sistema.co', 'admin123', 'Activo');

INSERT INTO TTrabajador (cIdentificacion, cNombre, cApellido, cPassword, cTelefono, nRolFK)
VALUES
  ('1234567890', 'Juan', 'Pérez', 'pass123', '3009876543', 1),
  ('0987654321', 'María', 'López', 'pass456', '3007654321', 2);

INSERT INTO TTrabajadorTienda (nTiendaFK, nTrabajadorFK) VALUES (1, 1), (1, 2);
