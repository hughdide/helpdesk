-- Fase 2: notas internas, categorías (ejecutar en helpdesk)

USE helpdesk;

-- A) Notas internas en historial (1 = solo agente/admin)
ALTER TABLE ticket_historial
ADD COLUMN es_interno TINYINT(1) NOT NULL DEFAULT 0 AFTER detalle;

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

ALTER TABLE tickets
ADD COLUMN categoria_id INT NULL AFTER prioridad;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_categoria
  FOREIGN KEY (categoria_id) REFERENCES categorias(id)
  ON DELETE SET NULL ON UPDATE CASCADE;
