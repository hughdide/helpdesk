-- Fase 3: SLA y registro de notificaciones (ejecutar en helpdesk)
-- Seguro para reimportar

USE helpdesk;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'sla_respuesta_limite'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE tickets ADD COLUMN sla_respuesta_limite DATETIME NULL AFTER cerrado_en',
  'SELECT ''sla_respuesta_limite ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'sla_resolucion_limite'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE tickets ADD COLUMN sla_resolucion_limite DATETIME NULL AFTER sla_respuesta_limite',
  'SELECT ''sla_resolucion_limite ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @existe := (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tickets' AND COLUMN_NAME = 'primera_respuesta_en'
);
SET @sql := IF(@existe = 0,
  'ALTER TABLE tickets ADD COLUMN primera_respuesta_en DATETIME NULL AFTER sla_resolucion_limite',
  'SELECT ''primera_respuesta_en ya existe'' AS info');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS notificaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id INT NULL,
  usuario_id INT NULL,
  email VARCHAR(120) NOT NULL,
  tipo VARCHAR(40) NOT NULL,
  asunto VARCHAR(200) NOT NULL,
  cuerpo TEXT NOT NULL,
  enviado TINYINT(1) NOT NULL DEFAULT 0,
  error_msg VARCHAR(255) NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notif_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE SET NULL,
  CONSTRAINT fk_notif_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- Rellenar límites SLA en tickets antiguos (según prioridad y fecha de alta)
UPDATE tickets SET
  sla_respuesta_limite = CASE LOWER(IFNULL(prioridad, 'media'))
    WHEN 'alta' THEN DATE_ADD(creado_en, INTERVAL 4 HOUR)
    WHEN 'baja' THEN DATE_ADD(creado_en, INTERVAL 24 HOUR)
    ELSE DATE_ADD(creado_en, INTERVAL 8 HOUR)
  END,
  sla_resolucion_limite = CASE LOWER(IFNULL(prioridad, 'media'))
    WHEN 'alta' THEN DATE_ADD(creado_en, INTERVAL 24 HOUR)
    WHEN 'baja' THEN DATE_ADD(creado_en, INTERVAL 72 HOUR)
    ELSE DATE_ADD(creado_en, INTERVAL 48 HOUR)
  END
WHERE sla_respuesta_limite IS NULL AND creado_en IS NOT NULL;
