"""Cálculo de SLA por prioridad (horas desde la creación del ticket)."""
from datetime import datetime, timedelta

# (horas primera respuesta, horas resolución)
SLA_HORAS = {
    'baja': (24, 72),
    'media': (8, 48),
    'alta': (4, 24),
}

RIESGO_FRACCION = 0.25  # último 25 % del plazo = en riesgo

# Fragmentos SQL reutilizables (alineados con evaluar_sla)
SQL_COND_RESPUESTA_VENCIDA = """
(
  (t.estado != 'Cerrado' AND t.primera_respuesta_en IS NULL
   AND t.sla_respuesta_limite IS NOT NULL AND NOW() > t.sla_respuesta_limite)
  OR
  (t.primera_respuesta_en IS NOT NULL AND t.sla_respuesta_limite IS NOT NULL
   AND t.primera_respuesta_en > t.sla_respuesta_limite)
)
"""

SQL_COND_RESOLUCION_VENCIDA = """
(
  (t.estado != 'Cerrado' AND t.sla_resolucion_limite IS NOT NULL
   AND NOW() > t.sla_resolucion_limite)
  OR
  (t.estado = 'Cerrado' AND t.cerrado_en IS NOT NULL AND t.sla_resolucion_limite IS NOT NULL
   AND t.cerrado_en > t.sla_resolucion_limite)
)
"""

SQL_COND_EN_RIESGO = """
(
  (
    t.estado != 'Cerrado'
    AND t.sla_respuesta_limite IS NOT NULL
    AND t.primera_respuesta_en IS NULL
    AND NOW() < t.sla_respuesta_limite
    AND TIMESTAMPDIFF(SECOND, NOW(), t.sla_respuesta_limite)
        <= TIMESTAMPDIFF(SECOND, t.creado_en, t.sla_respuesta_limite) * 0.25
  )
  OR
  (
    t.estado != 'Cerrado'
    AND t.primera_respuesta_en IS NOT NULL
    AND t.sla_resolucion_limite IS NOT NULL
    AND NOW() < t.sla_resolucion_limite
    AND TIMESTAMPDIFF(SECOND, NOW(), t.sla_resolucion_limite)
        <= TIMESTAMPDIFF(SECOND, t.creado_en, t.sla_resolucion_limite) * 0.25
  )
)
"""

def _normalizar_prioridad(prioridad):
    p = (prioridad or 'media').lower()
    return p if p in SLA_HORAS else 'media'


def _parse_fecha(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, str):
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                return datetime.strptime(valor[:19], fmt)
            except ValueError:
                continue
    return None


def calcular_limites_sla(prioridad, creado_en):
    p = _normalizar_prioridad(prioridad)
    h_resp, h_resol = SLA_HORAS[p]
    base = _parse_fecha(creado_en) or datetime.now()
    return (
        base + timedelta(hours=h_resp),
        base + timedelta(hours=h_resol),
    )


def _estado_plazo(ahora, limite, cumplido_en, cerrado=False):
    """Devuelve ok | cumplido | riesgo | vencido | pendiente."""
    if cumplido_en:
        lim = _parse_fecha(limite)
        cum = _parse_fecha(cumplido_en)
        if lim and cum and cum <= lim:
            return 'cumplido'
        if lim and cum and cum > lim:
            return 'vencido'
        return 'cumplido'

    if cerrado:
        return 'pendiente'

    lim = _parse_fecha(limite)
    if not lim:
        return 'pendiente'

    if ahora > lim:
        return 'vencido'

    total = (lim - (_parse_fecha(lim) - timedelta(hours=1))).total_seconds()  # fallback
    # usar creado implícito: fracción restante
    restante = (lim - ahora).total_seconds()
    duracion = (lim - ahora + (ahora - ahora)).total_seconds()
    # mejor: comparar con ventana desde ahora hasta limite vs ventana total
    # simplificado: riesgo si queda menos del 25% del tiempo hasta limite
    # estimamos inicio como lim - SLA no guardado aquí → usar heurística por restante absoluto
    if restante <= 3600 and restante > 0:  # <1h y no vencido
        return 'riesgo'
    # si queda poco % del plazo (necesitamos creado); se pasa desde fuera
    return 'pendiente'


def _estado_plazo_con_inicio(ahora, inicio, limite, cumplido_en):
    if cumplido_en:
        lim = _parse_fecha(limite)
        cum = _parse_fecha(cumplido_en)
        if lim and cum:
            return 'cumplido' if cum <= lim else 'vencido'
        return 'cumplido'

    lim = _parse_fecha(limite)
    ini = _parse_fecha(inicio)
    if not lim or not ini:
        return 'pendiente'

    if ahora > lim:
        return 'vencido'

    total = (lim - ini).total_seconds()
    restante = (lim - ahora).total_seconds()
    if total > 0 and restante / total <= RIESGO_FRACCION:
        return 'riesgo'
    return 'pendiente'


def _calcular_retraso_segundos(limite, cumplido_en, ahora, vencido):
    """Segundos de retraso respecto al límite si el plazo está vencido."""
    if not vencido:
        return None
    lim = _parse_fecha(limite)
    if not lim:
        return None
    ref = _parse_fecha(cumplido_en) if cumplido_en else ahora
    if not ref or ref <= lim:
        return None
    return int((ref - lim).total_seconds())


def formatear_retraso(segundos):
    """Texto legible para un retraso en segundos (p. ej. 2d 9h 27m)."""
    if segundos is None or segundos <= 0:
        return None
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    mins = (segundos % 3600) // 60
    if dias > 0:
        return f'{dias}d {horas}h {mins}m'
    if horas > 0:
        return f'{horas}h {mins}m'
    if mins > 0:
        return f'{mins}m'
    return f'{segundos}s'


def formatear_duracion(segundos):
    """Duración media legible (p. ej. 2d 5h o 45m)."""
    if segundos is None:
        return '—'
    total = int(round(segundos))
    if total <= 0:
        return '—'
    dias = total // 86400
    horas = (total % 86400) // 3600
    mins = (total % 3600) // 60
    if dias > 0:
        return f'{dias}d {horas}h'
    if horas > 0:
        return f'{horas}h {mins}m'
    return f'{mins}m'


def evaluar_sla(ticket):
    """Devuelve diccionario con estados de respuesta y resolución para plantillas."""
    ahora = datetime.now()
    prioridad = _normalizar_prioridad(ticket.get('prioridad'))
    h_resp, h_resol = SLA_HORAS[prioridad]
    creado = _parse_fecha(ticket.get('creado_en')) or ahora

    lim_resp = _parse_fecha(ticket.get('sla_respuesta_limite'))
    lim_resol = _parse_fecha(ticket.get('sla_resolucion_limite'))
    if not lim_resp or not lim_resol:
        lim_resp, lim_resol = calcular_limites_sla(prioridad, creado)

    primera = ticket.get('primera_respuesta_en')
    cerrado = ticket.get('cerrado_en')
    estado_ticket = ticket.get('estado')

    est_resp = _estado_plazo_con_inicio(ahora, creado, lim_resp, primera)
    est_resol = _estado_plazo_con_inicio(
        ahora, creado, lim_resol,
        cerrado if estado_ticket == 'Cerrado' else None,
    )

    if not primera and estado_ticket != 'Cerrado' and est_resp == 'pendiente':
        if ahora > lim_resp:
            est_resp = 'vencido'
        else:
            total = (lim_resp - creado).total_seconds()
            restante = (lim_resp - ahora).total_seconds()
            if total > 0 and restante / total <= RIESGO_FRACCION:
                est_resp = 'riesgo'

    if estado_ticket != 'Cerrado' and est_resol == 'pendiente':
        if ahora > lim_resol:
            est_resol = 'vencido'
        else:
            total = (lim_resol - creado).total_seconds()
            restante = (lim_resol - ahora).total_seconds()
            if total > 0 and restante / total <= RIESGO_FRACCION:
                est_resol = 'riesgo'

    if primera and est_resp == 'pendiente':
        est_resp = _estado_plazo_con_inicio(ahora, creado, lim_resp, primera)

    if estado_ticket == 'Cerrado' and cerrado and est_resol == 'pendiente':
        est_resol = _estado_plazo_con_inicio(ahora, creado, lim_resol, cerrado)

    peor = est_resp
    orden = {'vencido': 4, 'riesgo': 3, 'pendiente': 2, 'cumplido': 1, 'ok': 0}
    for e in (est_resp, est_resol):
        if orden.get(e, 0) > orden.get(peor, 0):
            peor = e

    deadline_activo = None
    tipo_deadline = None
    if estado_ticket != 'Cerrado':
        if not primera:
            deadline_activo = lim_resp
            tipo_deadline = 'respuesta'
        else:
            deadline_activo = lim_resol
            tipo_deadline = 'resolucion'

    retraso_resp = formatear_retraso(
        _calcular_retraso_segundos(lim_resp, primera, ahora, est_resp == 'vencido')
    )
    retraso_resol = formatear_retraso(
        _calcular_retraso_segundos(
            lim_resol,
            cerrado if estado_ticket == 'Cerrado' else None,
            ahora,
            est_resol == 'vencido',
        )
    )

    return {
        'prioridad': prioridad,
        'horas_respuesta': h_resp,
        'horas_resolucion': h_resol,
        'limite_respuesta': lim_resp,
        'limite_resolucion': lim_resol,
        'estado_respuesta': est_resp,
        'estado_resolucion': est_resol,
        'estado_global': peor,
        'primera_respuesta_en': primera,
        'retraso_respuesta': retraso_resp,
        'retraso_resolucion': retraso_resol,
        'deadline_activo': deadline_activo,
        'tipo_deadline': tipo_deadline,
    }


def etiqueta_estado(codigo):
    return {
        'cumplido': 'Cumplido',
        'vencido': 'Vencido',
        'riesgo': 'En riesgo',
        'pendiente': 'En plazo',
    }.get(codigo, codigo)


def actualizar_limites_ticket(cursor, conn, ticket_id, prioridad, creado_en):
    lim_resp, lim_resol = calcular_limites_sla(prioridad, creado_en)
    cursor.execute(
        """UPDATE tickets SET sla_respuesta_limite=%s, sla_resolucion_limite=%s
           WHERE id=%s""",
        (lim_resp.strftime('%Y-%m-%d %H:%M:%S'),
         lim_resol.strftime('%Y-%m-%d %H:%M:%S'),
         ticket_id),
    )
    conn.commit()
    return lim_resp, lim_resol


def marcar_primera_respuesta(cursor, conn, ticket_id):
    cursor.execute(
        """UPDATE tickets SET primera_respuesta_en = NOW()
           WHERE id = %s AND primera_respuesta_en IS NULL""",
        (ticket_id,),
    )
    conn.commit()
