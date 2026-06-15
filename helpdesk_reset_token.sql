-- Columnas para recuperación de contraseña por correo (opcional si la app ya las creó al arrancar)
USE helpdesk;

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64) NULL;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS reset_token_expira DATETIME NULL;
