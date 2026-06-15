"""Envío de correos y registro en tabla notificaciones."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config_mail as cfg
from db_notificaciones import insertar_registro


def _registrar(cursor, conn, email, tipo, asunto, cuerpo, ticket_id=None, usuario_id=None,
               enviado=0, error_msg=None):
    insertar_registro(
        cursor, conn, email, tipo, asunto, cuerpo,
        ticket_id=ticket_id, usuario_id=usuario_id,
        enviado=enviado, error_msg=error_msg,
    )


def enviar_correo(destinatario, asunto, cuerpo_texto, cuerpo_html=None):
    if not destinatario:
        return False, 'Sin destinatario'

    if not cfg.MAIL_ENABLED:
        return False, 'Correo desactivado (MAIL_ENABLED=0 en mail.env)'

    if not cfg.SMTP_USER or not cfg.SMTP_PASSWORD:
        return False, 'Faltan SMTP_USER o SMTP_PASSWORD en mail.env'

    msg = MIMEMultipart('alternative')
    msg['Subject'] = asunto
    msg['From'] = f'{cfg.MAIL_FROM_NAME} <{cfg.MAIL_FROM}>'
    msg['To'] = destinatario
    msg.attach(MIMEText(cuerpo_texto, 'plain', 'utf-8'))
    if cuerpo_html:
        msg.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=15) as server:
            if cfg.SMTP_USE_TLS:
                server.starttls()
            server.login(cfg.SMTP_USER, cfg.SMTP_PASSWORD)
            server.sendmail(cfg.MAIL_FROM, [destinatario], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)[:250]


def notificar(cursor, conn, email, tipo, asunto, cuerpo, ticket_id=None, usuario_id=None):
    if not email:
        return
    ok, err = enviar_correo(email, asunto, cuerpo)
    _registrar(
        cursor, conn, email, tipo, asunto, cuerpo,
        ticket_id=ticket_id, usuario_id=usuario_id,
        enviado=1 if ok else 0, error_msg=err,
    )


def url_ticket(ticket_id):
    return f'{cfg.APP_BASE_URL}/ticket/{ticket_id}'


def _cuerpo_ticket(ticket_id, titulo, mensaje):
    link = url_ticket(ticket_id)
    return (
        f'{mensaje}\n\n'
        f'Ticket #{ticket_id}: {titulo}\n'
        f'Ver en el helpdesk: {link}\n\n'
        f'— Galsoft Helpdesk'
    )


def emails_equipo_soporte(cursor):
    cursor.execute(
        "SELECT id, nombre, email FROM usuarios WHERE rol IN ('agente', 'admin') AND email IS NOT NULL"
    )
    return cursor.fetchall()


def on_ticket_nuevo(cursor, conn, ticket_id, titulo, cliente_nombre, cliente_email):
    asunto = f'[Helpdesk] Nuevo ticket #{ticket_id}: {titulo}'
    cuerpo_cli = _cuerpo_ticket(
        ticket_id, titulo,
        f'Hola {cliente_nombre},\n\nHemos registrado tu petición. El equipo de soporte la revisará pronto.',
    )
    if cliente_email:
        notificar(cursor, conn, cliente_email, 'ticket_creado_cliente', asunto, cuerpo_cli,
                  ticket_id=ticket_id)

    cuerpo_eq = _cuerpo_ticket(
        ticket_id, titulo,
        f'Nueva petición de {cliente_nombre}. Revisa el panel y asigna un agente si procede.',
    )
    for u in emails_equipo_soporte(cursor):
        notificar(cursor, conn, u['email'], 'ticket_nuevo_equipo', asunto, cuerpo_eq,
                  ticket_id=ticket_id, usuario_id=u['id'])


def aviso_agente_a_cliente(cursor, conn, ticket, mensaje):
    """
    Envía correo al cliente cuando un agente/admin comenta en público.
    Devuelve None si se envió bien; si no, texto para mostrar al agente.
    """
    tid = ticket['id']
    titulo = ticket['titulo']
    email_cli = ticket.get('cliente_email')

    if not email_cli or str(email_cli).strip() == '':
        nombre = ticket.get('cliente_nombre', 'el cliente')
        return (
            'Comentario guardado, pero ' + nombre + ' no tiene correo en su ficha. '
            'Revísalo en Usuarios (admin).'
        )

    if not cfg.MAIL_ENABLED:
        return (
            'Comentario guardado, pero el correo está desactivado. '
            'Copia mail.env.example a mail.env, pon MAIL_ENABLED=1 y configura SMTP.'
        )

    asunto = '[Helpdesk] Actualización ticket #' + str(tid)
    cuerpo = _cuerpo_ticket(
        tid,
        titulo,
        'Hola ' + str(ticket.get('cliente_nombre', '')) + ',\n\n'
        'El equipo de soporte ha respondido:\n\n' + mensaje,
    )
    ok, err = enviar_correo(email_cli, asunto, cuerpo)
    _registrar(
        cursor, conn, email_cli, 'comentario_agente', asunto, cuerpo,
        ticket_id=tid, usuario_id=ticket.get('usuario_id'),
        enviado=1 if ok else 0, error_msg=err,
    )
    if ok:
        return None
    return 'Comentario guardado, pero no se pudo enviar el correo: ' + str(err)


def on_comentario_publico(cursor, conn, ticket, autor_rol, autor_nombre, mensaje):
    tid = ticket['id']
    titulo = ticket['titulo']
    asunto = '[Helpdesk] Actualización ticket #' + str(tid)

    if autor_rol == 'cliente':
        cuerpo = _cuerpo_ticket(
            tid, titulo,
            'El cliente ' + autor_nombre + ' ha añadido un comentario:\n\n' + mensaje,
        )
        if ticket.get('agente_email'):
            notificar(cursor, conn, ticket['agente_email'], 'comentario_cliente', asunto, cuerpo,
                      ticket_id=tid, usuario_id=ticket.get('agente_id'))
        else:
            for u in emails_equipo_soporte(cursor):
                notificar(cursor, conn, u['email'], 'comentario_cliente', asunto, cuerpo,
                          ticket_id=tid, usuario_id=u['id'])
    else:
        return aviso_agente_a_cliente(cursor, conn, ticket, mensaje)


def on_estado_cambiado(cursor, conn, ticket, estado_nuevo):
    tid = ticket['id']
    titulo = ticket['titulo']
    asunto = f'[Helpdesk] Ticket #{tid} — {estado_nuevo}'
    cuerpo = _cuerpo_ticket(
        tid, titulo,
        f'Hola {ticket.get("cliente_nombre", "")},\n\n'
        f'El estado de tu petición es ahora: {estado_nuevo}.',
    )
    if ticket.get('cliente_email'):
        notificar(cursor, conn, ticket['cliente_email'], 'cambio_estado', asunto, cuerpo,
                  ticket_id=tid, usuario_id=ticket.get('usuario_id'))


def on_asignacion(cursor, conn, ticket, nombre_agente, agente_id, agente_email):
    if not agente_email:
        return
    tid = ticket['id']
    asunto = f'[Helpdesk] Ticket #{tid} asignado a ti'
    cuerpo = _cuerpo_ticket(
        tid, ticket['titulo'],
        f'Hola {nombre_agente},\n\nSe te ha asignado el ticket #{tid}.',
    )
    notificar(cursor, conn, agente_email, 'asignacion', asunto, cuerpo,
              ticket_id=tid, usuario_id=agente_id)


def enviar_recuperacion_contrasena(cursor, conn, usuario, token):
    """Envía enlace para restablecer o cambiar contraseña."""
    link = f'{cfg.APP_BASE_URL}/reset/{token}'
    nombre = usuario.get('nombre', '')
    email = usuario['email']
    asunto = '[Helpdesk] Restablecer contraseña'
    cuerpo = (
        f'Hola {nombre},\n\n'
        f'Has solicitado restablecer tu contraseña en Galsoft Helpdesk.\n\n'
        f'Abre este enlace (válido 24 horas):\n{link}\n\n'
        f'Si no lo solicitaste, ignora este mensaje.\n\n'
        f'— Galsoft Helpdesk'
    )
    notificar(
        cursor, conn, email, 'recuperar_contrasena', asunto, cuerpo,
        usuario_id=usuario['id'],
    )


def on_sla_vencido(cursor, conn, ticket, tipo_sla):
    """Aviso a equipo cuando un SLA está vencido (al consultar o actualizar)."""
    asunto = f'[Helpdesk] SLA {tipo_sla} vencido — ticket #{ticket["id"]}'
    cuerpo = _cuerpo_ticket(
        ticket['id'], ticket['titulo'],
        f'El ticket #{ticket["id"]} ha superado el plazo de {tipo_sla}. Prioridad: {ticket.get("prioridad")}.',
    )
    for u in emails_equipo_soporte(cursor):
        notificar(cursor, conn, u['email'], f'sla_{tipo_sla}', asunto, cuerpo,
                  ticket_id=ticket['id'], usuario_id=u['id'])
