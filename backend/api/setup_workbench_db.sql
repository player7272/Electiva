-- Script para preparar la base de datos local de Workbench para la API
-- Ejecutar con un usuario administrador (root) en MySQL Workbench.

CREATE DATABASE IF NOT EXISTS ecosistema_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'api_user'@'localhost' IDENTIFIED BY 'api_password_seguro';
CREATE USER IF NOT EXISTS 'api_user'@'127.0.0.1' IDENTIFIED BY 'api_password_seguro';

GRANT ALL PRIVILEGES ON ecosistema_db.* TO 'api_user'@'localhost';
GRANT ALL PRIVILEGES ON ecosistema_db.* TO 'api_user'@'127.0.0.1';

FLUSH PRIVILEGES;
