-- Fase 2: notas internas, categorías (ejecutar en helpdesk)
-- Seguro para reimportar: no falla si ya aplicaste parte del script

USE helpdesk;

-- A) Notas internas en historial (1 = solo agente/admin)
SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ticket_historial'
    AND COLUMN_NAME = 'es_interno'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE ticket_historial ADD COLUMN es_interno TINYINT(1) NOT NULL DEFAULT 0 AFTER detalle',
  'SELECT ''Columna es_interno ya existe'' AS info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- D) Categorías de tickets
CREATE TABLE IF NOT EXISTS categorias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE
);

INSERT IGNORE INTO categorias (nombre) VALUES
('General'),
('Hardware'),
('Software'),
('Red'),
('Facturación'),
('Otros');

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tickets'
    AND COLUMN_NAME = 'categoria_id'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE tickets ADD COLUMN categoria_id INT NULL AFTER prioridad',
  'SELECT ''Columna categoria_id ya existe'' AS info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tickets'
    AND CONSTRAINT_NAME = 'fk_tickets_categoria'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE tickets ADD CONSTRAINT fk_tickets_categoria FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL ON UPDATE CASCADE',
  'SELECT ''FK fk_tickets_categoria ya existe'' AS info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
