#"""Compatibilidad con tabla notificaciones."""

_COLUMNAS_CACHE = {}


def columnas_tabla(cursor, tabla):
    if tabla in _COLUMNAS_CACHE:
        return _COLUMNAS_CACHE[tabla]
    cursor.execute(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        (tabla,),
    )
    cols = {r['COLUMN_NAME'] for r in cursor.fetchall()}
    _COLUMNAS_CACHE[tabla] = cols
    return cols


def columna_fecha(cols):
    for nombre in ('creado_en', 'fecha', 'fecha_envio', 'created_at'):
        if nombre in cols:
            return nombre
    return 'id'


def normalizar_fila(fila, cols):
    """Unifica nombres para plantillas y mailer."""
    if 'creado_en' not in fila or fila.get('creado_en') is None:
        for alt in ('fecha', 'fecha_envio', 'created_at'):
            if fila.get(alt):
                fila['creado_en'] = fila[alt]
                break
    if not fila.get('tipo'):
        fila['tipo'] = fila.get('tipo_notificacion') or fila.get('evento') or '—'
    if not fila.get('asunto'):
        fila['asunto'] = fila.get('titulo') or fila.get('mensaje', '')[:80] or '—'
    if 'email' not in fila or not fila.get('email'):
        fila['email'] = fila.get('correo') or fila.get('destinatario') or '—'
    if 'enviado' not in fila:
        fila['enviado'] = 1 if fila.get('leida') or fila.get('enviada') else 0
    if 'error_msg' not in fila:
        fila['error_msg'] = fila.get('error') or fila.get('error_mensaje')
    return fila


def listar_historial(cursor, limite=100):
    cols = columnas_tabla(cursor, 'notificaciones')
    if not cols:
        return []

    fecha_col = columna_fecha(cols)
    sql = f"""
        SELECT n.*, t.titulo AS ticket_titulo
        FROM notificaciones n
        LEFT JOIN tickets t ON n.ticket_id = t.id
        ORDER BY n.`{fecha_col}` DESC
        LIMIT %s
    """
    cursor.execute(sql, (limite,))
    return [normalizar_fila(dict(r), cols) for r in cursor.fetchall()]


def _primera_columna(cols, opciones):
    for nombre in opciones:
        if nombre in cols:
            return nombre
    return None


def insertar_registro(cursor, conn, email, tipo, asunto, cuerpo,
                      ticket_id=None, usuario_id=None, enviado=0, error_msg=None):
    cols = columnas_tabla(cursor, 'notificaciones')
    if not cols:
        return

    campos_valores = []
    if ticket_id is not None and 'ticket_id' in cols:
        campos_valores.append(('ticket_id', ticket_id))
    if usuario_id is not None and 'usuario_id' in cols:
        campos_valores.append(('usuario_id', usuario_id))

    col_email = _primera_columna(cols, ('email', 'correo', 'destinatario'))
    if col_email:
        campos_valores.append((col_email, email))

    col_tipo = _primera_columna(cols, ('tipo', 'tipo_notificacion', 'evento'))
    if col_tipo:
        campos_valores.append((col_tipo, tipo))

    col_asunto = _primera_columna(cols, ('asunto', 'titulo'))
    if col_asunto:
        campos_valores.append((col_asunto, asunto))

    col_cuerpo = _primera_columna(cols, ('cuerpo', 'mensaje'))
    if col_cuerpo:
        campos_valores.append((col_cuerpo, cuerpo))

    col_enviado = _primera_columna(cols, ('enviado', 'enviada', 'leida'))
    if col_enviado:
        campos_valores.append((col_enviado, enviado))

    col_error = _primera_columna(cols, ('error_msg', 'error', 'error_mensaje'))
    if col_error and error_msg:
        campos_valores.append((col_error, error_msg))

    if not campos_valores:
        return

    usar = [c for c, _ in campos_valores]
    valores = [v for _, v in campos_valores]
    placeholders = ', '.join(['%s'] * len(usar))
    campos_sql = ', '.join(f'`{c}`' for c in usar)
    try:
        cursor.execute(
            f'INSERT INTO notificaciones ({campos_sql}) VALUES ({placeholders})',
            tuple(valores),
        )
        conn.commit()
    except Exception:
        conn.rollback()
