-- Fase 1: agente asignado + historial de actividad
-- Ejecutar en phpMyAdmin sobre la base de datos helpdesk

USE helpdesk;

-- Agente que tramita el ticket (NULL = sin asignar)
ALTER TABLE tickets
ADD COLUMN agente_id INT NULL AFTER usuario_id;

ALTER TABLE tickets
ADD COLUMN cerrado_en DATETIME NULL AFTER agente_id;

ALTER TABLE tickets
ADD CONSTRAINT fk_tickets_agente
  FOREIGN KEY (agente_id) REFERENCES usuarios(id)
  ON DELETE SET NULL ON UPDATE CASCADE;

CREATE TABLE ticket_historial (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticket_id INT NOT NULL,
  usuario_id INT NOT NULL,
  tipo VARCHAR(30) NOT NULL,
  detalle TEXT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_hist_ticket
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
  CONSTRAINT fk_hist_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
