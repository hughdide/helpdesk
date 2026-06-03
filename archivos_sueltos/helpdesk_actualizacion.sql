-- Ejecutar en la base de datos helpdesk (phpMyAdmin / MySQL)
USE helpdesk;

ALTER TABLE tickets
ADD COLUMN prioridad VARCHAR(20) NOT NULL DEFAULT 'media'
AFTER estado;

-- Valores válidos: baja, media, alta
