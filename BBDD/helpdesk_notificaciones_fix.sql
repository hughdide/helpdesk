-- Ajusta la tabla notificaciones si ya existía con otro esquema (ejecutar en helpdesk)

USE helpdesk;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'creado_en'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN creado_en DATETIME NULL DEFAULT CURRENT_TIMESTAMP',
  'SELECT ''creado_en ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @tiene_fecha := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'fecha'
);
SET @sql := IF(@tiene_fecha > 0,
  'UPDATE notificaciones SET creado_en = COALESCE(creado_en, fecha)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'email'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN email VARCHAR(120) NULL',
  'SELECT ''email ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'tipo'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN tipo VARCHAR(40) NULL',
  'SELECT ''tipo ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'asunto'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN asunto VARCHAR(200) NULL',
  'SELECT ''asunto ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'cuerpo'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN cuerpo TEXT NULL',
  'SELECT ''cuerpo ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'enviado'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN enviado TINYINT(1) NOT NULL DEFAULT 0',
  'SELECT ''enviado ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'notificaciones' AND COLUMN_NAME = 'error_msg'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE notificaciones ADD COLUMN error_msg VARCHAR(255) NULL',
  'SELECT ''error_msg ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
