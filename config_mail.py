"""
Configuración de correo para el helpdesk.
Copia mail.env.example a mail.env o define variables de entorno.

Para Gmail: cuenta con contraseña de aplicación, SMTP_PORT=587, SMTP_USE_TLS=1
"""
import os
from pathlib import Path

_env_file = Path(__file__).parent / 'mail.env'
if _env_file.exists():
    for line in _env_file.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip()

MAIL_ENABLED = os.environ.get('MAIL_ENABLED', '0').strip() in ('1', 'true', 'yes')
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', '1').strip() in ('1', 'true', 'yes')
MAIL_FROM = os.environ.get('MAIL_FROM', SMTP_USER or 'helpdesk@galsoft.local')
MAIL_FROM_NAME = os.environ.get('MAIL_FROM_NAME', 'Galsoft Helpdesk')
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://127.0.0.1:5000')
