from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, send_file
import mysql.connector
import os
import io
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from sla import (
    calcular_limites_sla,
    evaluar_sla,
    etiqueta_estado,
    actualizar_limites_ticket,
    marcar_primera_respuesta,
)
import mailer
import config_mail
from db_notificaciones import listar_historial as listar_notificaciones_db


# Conexión a MySQL
mibd = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="helpdesk"
)
micursor = mibd.cursor(dictionary=True)

# Configuración Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)


app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.template_filter('fecha_es')
def fecha_es(valor):
    """Muestra fechas como DD-MM-AAAA HH:MM"""
    if valor is None or valor == '':
        return ''
    if isinstance(valor, datetime):
        dt = valor
    else:
        texto = str(valor)[:19]
        try:
            dt = datetime.strptime(texto, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                dt = datetime.strptime(texto[:10], '%Y-%m-%d')
            except ValueError:
                return str(valor)
    return dt.strftime('%d-%m-%Y %H:%M')

# Consulta base reutilizable: ticket + nombre/email del cliente y agente + nombre de categoría.
SQL_TICKET_BASE = """
SELECT t.*, c.nombre AS cliente_nombre, c.email AS cliente_email,
       a.nombre AS agente_nombre, a.email AS agente_email,
       cat.nombre AS categoria_nombre
FROM tickets t
INNER JOIN usuarios c ON t.usuario_id = c.id
LEFT JOIN usuarios a ON t.agente_id = a.id
LEFT JOIN categorias cat ON t.categoria_id = cat.id
"""

# Añade a cada ticket del listado el estado SLA (en plazo, riesgo, vencido, etc.).
def enriquecer_sla_listado(tickets):
    for t in tickets:
        t['sla'] = evaluar_sla(t)
    return tickets


# Guarda una línea en ticket_historial (comentario, cambio de estado, asignación, etc.).
def registrar_historial(ticket_id, usuario_id, tipo, detalle, es_interno=0):
    sql = """INSERT INTO ticket_historial (ticket_id, usuario_id, tipo, detalle, es_interno)
             VALUES (%s, %s, %s, %s, %s)"""
    micursor.execute(sql, (ticket_id, usuario_id, tipo, detalle, es_interno))
    mibd.commit()


# Devuelve todas las categorías ordenadas por nombre (formularios y filtros).
def listar_categorias():
    sql = "SELECT id, nombre FROM categorias ORDER BY nombre ASC"
    micursor.execute(sql)
    return micursor.fetchall()


# Lista tickets según rol y filtros (estado, prioridad, categoría, búsqueda, SLA, etc.).
def listar_tickets_consulta(rol, usuario_id, filtros_dict):
    sql = SQL_TICKET_BASE
    params = []
    condiciones = []

    # Cliente: solo sus propios tickets
    if rol == 'cliente':
        condiciones.append("t.usuario_id = %s")
        params.append(usuario_id)

    # Filtro por estado (Abierto, En proceso, Cerrado)
    if filtros_dict.get('estado'):
        condiciones.append("t.estado = %s")
        params.append(filtros_dict['estado'])

    # Filtro por prioridad (baja, media, alta)
    if filtros_dict.get('prioridad'):
        condiciones.append("t.prioridad = %s")
        params.append(filtros_dict['prioridad'])

    # Filtro por categoría
    if filtros_dict.get('categoria_id'):
        condiciones.append("t.categoria_id = %s")
        params.append(filtros_dict['categoria_id'])

    # Agente/admin: solo tickets asignados al usuario actual
    if filtros_dict.get('mis_tickets') and rol in ['agente', 'admin']:
        condiciones.append("t.agente_id = %s")
        params.append(usuario_id)

    # Agente/admin: tickets sin agente asignado
    if filtros_dict.get('sin_asignar') and rol in ['agente', 'admin']:
        condiciones.append("t.agente_id IS NULL")

    # Búsqueda por texto en título o descripción
    if filtros_dict.get('buscar'):
        like = f"%{filtros_dict['buscar']}%"
        condiciones.append("(t.titulo LIKE %s OR t.descripcion LIKE %s)")
        params.extend([like, like])

    # Agente/admin: tickets abiertos con SLA de respuesta o resolución vencido
    if filtros_dict.get('sla') == 'vencido' and filtros_dict.get('rol') in ['agente', 'admin']:
        condiciones.append("t.estado != 'Cerrado'")
        condiciones.append(
            "( (t.primera_respuesta_en IS NULL AND NOW() > t.sla_respuesta_limite) "
            "OR (t.estado != 'Cerrado' AND NOW() > t.sla_resolucion_limite) )"
        )

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY t.creado_en DESC"
    micursor.execute(sql, tuple(params))
    return micursor.fetchall()


# Obtiene un ticket por id; el cliente solo puede ver los suyos.
def obtener_ticket(ticket_id, rol, usuario_id):
    sql = SQL_TICKET_BASE + " WHERE t.id = %s"
    params = [ticket_id]
    if rol == 'cliente':
        sql += " AND t.usuario_id = %s"
        params.append(usuario_id)
    micursor.execute(sql, tuple(params))
    return micursor.fetchone()


# Historial de un ticket; el cliente no ve entradas con es_interno = 1.
def listar_historial_ticket(ticket_id, rol):
    sql = """SELECT h.*, u.nombre AS usuario_nombre
             FROM ticket_historial h
             INNER JOIN usuarios u ON h.usuario_id = u.id
             WHERE h.ticket_id = %s"""
    params = [ticket_id]
    if rol == 'cliente':
        sql += " AND h.es_interno = 0"
    sql += " ORDER BY h.fecha DESC, h.id DESC"
    micursor.execute(sql, tuple(params))
    return micursor.fetchall()


# Lista usuarios con rol agente o admin (para asignar tickets en gestión).
def listar_agentes():
    sql = "SELECT id, nombre FROM usuarios WHERE rol IN ('agente', 'admin') ORDER BY nombre ASC"
    micursor.execute(sql)
    return micursor.fetchall()


# Inicio — listado de tickets (con filtros). Cliente ve solo los suyos; agente/admin ven todos.
@app.route("/")
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    rol = session['usuario_rol']
    usuario_id = session['usuario_id']
    filtros = {
        'estado': request.args.get('estado', '').strip(),
        'prioridad': request.args.get('prioridad', '').strip(),
        'categoria_id': request.args.get('categoria_id', '').strip(),
        'buscar': request.args.get('buscar', '').strip(),
        'mis_tickets': request.args.get('mis_tickets') == '1',
        'sin_asignar': request.args.get('sin_asignar') == '1',
        'sla': request.args.get('sla', '').strip(),
        'rol': rol,
    }
    if filtros['categoria_id']:
        filtros['categoria_id'] = int(filtros['categoria_id'])
    else:
        filtros['categoria_id'] = None

    tickets = listar_tickets_consulta(rol, usuario_id, filtros)
    if rol in ['agente', 'admin']:
        tickets = enriquecer_sla_listado(tickets)
    categorias = listar_categorias()
    return render_template(
        "index.html",
        tickets=tickets,
        rol=rol,
        filtros=filtros,
        categorias=categorias,
        etiqueta_estado=etiqueta_estado,
    )


# Crear ticket nuevo. GET muestra formulario; POST guarda en BD, historial y aviso por correo.
@app.route('/ticket/nuevo', methods=['GET', 'POST'])
def new_ticket():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    archivo = None

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        usuario_id = session['usuario_id']  # CORRECTO
        archivo = request.files.get('archivo')

        filename = None
        archivo_blob = None

        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            archivo_blob = archivo.read()

        prioridad = request.form.get('prioridad', 'media')
        if prioridad not in ('baja', 'media', 'alta'):
            prioridad = 'media'

        categoria_id = request.form.get('categoria_id', '').strip()
        categoria_id = int(categoria_id) if categoria_id else None

        ahora = datetime.now()
        lim_resp, lim_resol = calcular_limites_sla(prioridad, ahora)
        sql = """INSERT INTO tickets (
                    titulo, descripcion, archivo, archivo_blob, usuario_id, prioridad, categoria_id,
                    sla_respuesta_limite, sla_resolucion_limite
                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        valores = (
            titulo, descripcion, filename, archivo_blob, usuario_id, prioridad, categoria_id,
            lim_resp.strftime('%Y-%m-%d %H:%M:%S'),
            lim_resol.strftime('%Y-%m-%d %H:%M:%S'),
        )
        micursor.execute(sql, valores)
        id_ticket = micursor.lastrowid
        mibd.commit()

        registrar_historial(id_ticket, usuario_id, 'creado', f'Ticket creado: {titulo}')
        if filename:
            registrar_historial(id_ticket, usuario_id, 'archivo', f'Archivo adjunto: {filename}')

        micursor.execute(
            "SELECT nombre, email FROM usuarios WHERE id = %s", (usuario_id,)
        )
        cli = micursor.fetchone()
        try:
            mailer.on_ticket_nuevo(
                micursor, mibd, id_ticket, titulo,
                cli['nombre'] if cli else '', cli['email'] if cli else None,
            )
        except Exception:
            pass

        flash("Petición creada correctamente.")
        return redirect(url_for('ticket_detalle', id=id_ticket))

    return render_template('new_ticket.html', categorias=listar_categorias())


# Iniciar sesión. Comprueba email y contraseña y guarda usuario en session.
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM usuarios WHERE email = %s"
        micursor.execute(sql, (email,))
        usuario = micursor.fetchone()

        if usuario and check_password_hash(usuario['password'], password):
            session.permanent = False
            session['usuario_id'] = usuario['id']
            session['usuario_nombre'] = usuario['nombre']
            session['usuario_rol'] = usuario['rol']
            flash(f"Bienvenido/a, {usuario['nombre']}.")
            return redirect(url_for('index'))
        else:
            flash("Correo o contraseña incorrectos.")
            return render_template("login.html")

    return render_template("login.html")


# Registro público. Crea cuenta nueva con rol cliente.
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        rol = 'cliente'

        # Encriptar contraseña
        password_hash = generate_password_hash(password)

        sql = "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)"
        valores = (nombre, email, password_hash, rol)

        try:
            micursor.execute(sql, valores)
            mibd.commit()
            flash("Cuenta creada correctamente. Ya puedes iniciar sesión.")
            return redirect(url_for('login'))
        except:
            flash("Ese correo ya está registrado.")
            return redirect(url_for('register'))

    return render_template("register.html")


# Cerrar sesión. Borra los datos de session y vuelve al login.
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for('login'))


# Descargar archivo adjunto de un ticket (desde la base de datos).
@app.route('/descargar/<int:id>')
def descargar_archivo(id):
    sql = "SELECT archivo, archivo_blob FROM tickets WHERE id = %s"
    micursor.execute(sql, (id,))
    resultado = micursor.fetchone()

    if resultado and resultado['archivo_blob']:
        nombre = resultado['archivo']
        contenido = resultado['archivo_blob']

        return send_file(
            io.BytesIO(contenido),
            download_name=nombre,
            as_attachment=True
        )
    else:
        flash("Archivo no encontrado.")
        return redirect(url_for('index'))
    

# Detalle del ticket. Ver información, historial, comentar, tomar ticket y gestionar (agente/admin).
@app.route("/ticket/<int:id>", methods=['GET', 'POST'])
def ticket_detalle(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    rol = session['usuario_rol']
    usuario_id = session['usuario_id']
    ticket = obtener_ticket(id, rol, usuario_id)
    if not ticket:
        flash("Ticket no encontrado o sin permiso.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        accion = request.form.get('accion', '')

        if accion == 'comentario':
            mensaje = request.form.get('mensaje', '').strip()
            if mensaje:
                es_interno = 0
                if rol in ['agente', 'admin'] and request.form.get('es_interno') == '1':
                    es_interno = 1
                tipo_hist = 'nota_interna' if es_interno else 'comentario'
                registrar_historial(id, usuario_id, tipo_hist, mensaje, es_interno)
                if not es_interno:
                    if rol in ['agente', 'admin']:
                        marcar_primera_respuesta(micursor, mibd, id)
                    if rol == 'cliente':
                        try:
                            mailer.on_comentario_publico(
                                micursor, mibd, ticket, rol,
                                session['usuario_nombre'], mensaje,
                            )
                        except Exception:
                            pass
                        flash("Comentario guardado.")
                    else:
                        aviso_mail = mailer.aviso_agente_a_cliente(micursor, mibd, ticket, mensaje)
                        if aviso_mail:
                            flash(aviso_mail)
                        else:
                            flash("Comentario guardado. Se ha enviado un correo al cliente.")
                else:
                    flash("Nota interna guardada (solo equipo).")
            return redirect(url_for('ticket_detalle', id=id))

        if accion == 'tomar' and rol in ['agente', 'admin']:
            if not ticket.get('agente_id'):
                sql = "UPDATE tickets SET agente_id = %s, estado = %s WHERE id = %s"
                nuevo_estado = 'En proceso' if ticket['estado'] == 'Abierto' else ticket['estado']
                micursor.execute(sql, (usuario_id, nuevo_estado, id))
                mibd.commit()
                registrar_historial(id, usuario_id, 'asignacion', f'Ticket asignado a {session["usuario_nombre"]}')
                if nuevo_estado != ticket['estado']:
                    registrar_historial(id, usuario_id, 'estado', f"Estado: {ticket['estado']} → {nuevo_estado}")
                micursor.execute("SELECT email FROM usuarios WHERE id = %s", (usuario_id,))
                ag = micursor.fetchone()
                try:
                    mailer.on_asignacion(
                        micursor, mibd, ticket, session['usuario_nombre'],
                        usuario_id, ag['email'] if ag else None,
                    )
                except Exception:
                    pass
                flash("Ticket asignado correctamente.")
            return redirect(url_for('ticket_detalle', id=id))

        if accion == 'gestionar' and rol in ['agente', 'admin']:
            nuevo_estado = request.form['estado']
            prioridad = request.form.get('prioridad', 'media')
            comentario = request.form.get('comentario', '').strip()
            if prioridad not in ('baja', 'media', 'alta'):
                prioridad = 'media'

            agente_id = ticket.get('agente_id')
            if rol == 'admin':
                agente_form = request.form.get('agente_id', '').strip()
                agente_id = int(agente_form) if agente_form else None
            elif nuevo_estado == 'En proceso' and not agente_id:
                agente_id = usuario_id

            cerrado_en = ticket.get('cerrado_en')
            if nuevo_estado == 'Cerrado' and ticket['estado'] != 'Cerrado':
                cerrado_en = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif nuevo_estado != 'Cerrado':
                cerrado_en = None

            sql = """UPDATE tickets SET estado=%s, prioridad=%s, comentario_estado=%s,
                     agente_id=%s, cerrado_en=%s WHERE id=%s"""
            if (ticket.get('prioridad') or 'media') != prioridad:
                actualizar_limites_ticket(
                    micursor, mibd, id, prioridad, ticket.get('creado_en'),
                )

            micursor.execute(sql, (nuevo_estado, prioridad, comentario, agente_id, cerrado_en, id))
            mibd.commit()

            if ticket['estado'] != nuevo_estado:
                registrar_historial(id, usuario_id, 'estado', f"Estado: {ticket['estado']} → {nuevo_estado}")
                try:
                    mailer.on_estado_cambiado(micursor, mibd, ticket, nuevo_estado)
                except Exception:
                    pass
            if (ticket.get('prioridad') or 'media') != prioridad:
                registrar_historial(id, usuario_id, 'prioridad', f"Prioridad: {ticket.get('prioridad', 'media')} → {prioridad}")
            if ticket.get('agente_id') != agente_id:
                nombre_agente = 'Sin asignar'
                email_agente = None
                if agente_id:
                    micursor.execute(
                        "SELECT nombre, email FROM usuarios WHERE id=%s", (agente_id,)
                    )
                    fila = micursor.fetchone()
                    if fila:
                        nombre_agente = fila['nombre']
                        email_agente = fila['email']
                registrar_historial(id, usuario_id, 'asignacion', f'Agente asignado: {nombre_agente}')
                if agente_id:
                    try:
                        mailer.on_asignacion(
                            micursor, mibd, ticket, nombre_agente, agente_id, email_agente,
                        )
                    except Exception:
                        pass
            if comentario:
                es_interno = 1 if request.form.get('comentario_interno') == '1' else 0
                tipo_hist = 'nota_interna' if es_interno else 'comentario'
                registrar_historial(id, usuario_id, tipo_hist, comentario, es_interno)
                if not es_interno:
                    marcar_primera_respuesta(micursor, mibd, id)
                    aviso_mail = mailer.aviso_agente_a_cliente(micursor, mibd, ticket, comentario)
                    if aviso_mail:
                        flash("Ticket actualizado. " + aviso_mail)
                    else:
                        flash("Ticket actualizado. Se ha enviado un correo al cliente.")
                    return redirect(url_for('ticket_detalle', id=id))

            flash("Ticket actualizado.")
            return redirect(url_for('ticket_detalle', id=id))

    historial = listar_historial_ticket(id, rol)
    agentes = listar_agentes() if rol == 'admin' else []
    sla_info = evaluar_sla(ticket)
    return render_template(
        'ticket_detalle.html',
        ticket=ticket,
        historial=historial,
        rol=rol,
        agentes=agentes,
        sla=sla_info,
        etiqueta_estado=etiqueta_estado,
        mail_habilitado=config_mail.MAIL_ENABLED,
    )


# Listado de usuarios del sistema (solo administrador).
@app.route('/usuarios')
def listar_usuarios():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('usuario_rol') != 'admin':
        flash("Solo administradores pueden gestionar usuarios.")
        return redirect(url_for('index'))

    buscar = request.args.get('q', '').strip()
    if buscar:
        like = f"%{buscar}%"
        sql = """SELECT id, nombre, email, rol FROM usuarios
                 WHERE nombre LIKE %s OR email LIKE %s
                 ORDER BY nombre ASC"""
        micursor.execute(sql, (like, like))
    else:
        sql = "SELECT id, nombre, email, rol FROM usuarios ORDER BY nombre ASC"
        micursor.execute(sql)

    usuarios = micursor.fetchall()
    return render_template('usuarios.html', usuarios=usuarios, buscar=buscar)


# Editar usuario — nombre, email, rol y contraseña (solo administrador).
@app.route('/usuario/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('usuario_rol') != 'admin':
        flash("Solo administradores pueden editar usuarios.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip().lower()
        rol = request.form['rol']
        password_nueva = request.form.get('password', '').strip()

        if rol not in ('cliente', 'agente', 'admin'):
            flash("Rol no válido.")
            return redirect(url_for('editar_usuario', id=id))

        if password_nueva:
            password_hash = generate_password_hash(password_nueva)
            sql = """UPDATE usuarios SET nombre=%s, email=%s, rol=%s, password=%s
                     WHERE id=%s"""
            valores = (nombre, email, rol, password_hash, id)
        else:
            sql = "UPDATE usuarios SET nombre=%s, email=%s, rol=%s WHERE id=%s"
            valores = (nombre, email, rol, id)

        try:
            micursor.execute(sql, valores)
            mibd.commit()
            flash("Usuario actualizado correctamente.")
            return redirect(url_for('listar_usuarios'))
        except mysql.connector.Error:
            flash("No se pudo guardar. ¿El correo ya existe?")
            return redirect(url_for('editar_usuario', id=id))

    sql = "SELECT id, nombre, email, rol FROM usuarios WHERE id = %s"
    micursor.execute(sql, (id,))
    usuario = micursor.fetchone()
    if not usuario:
        flash("Usuario no encontrado.")
        return redirect(url_for('listar_usuarios'))

    return render_template('editar_usuario.html', usuario=usuario)


# Gestionar categorías de tickets — listar y crear nuevas (solo administrador).
@app.route('/categorias', methods=['GET', 'POST'])
def gestionar_categorias():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('usuario_rol') != 'admin':
        flash("Solo administradores pueden gestionar categorías.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if nombre:
            try:
                micursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nombre,))
                mibd.commit()
                flash("Categoría creada.")
            except mysql.connector.Error:
                flash("Esa categoría ya existe.")
        return redirect(url_for('gestionar_categorias'))

    return render_template('categorias.html', categorias=listar_categorias())


# Panel de estadísticas — totales, SLA, gráficos y últimos tickets (agente y administrador).
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('usuario_rol') not in ['agente', 'admin']:
        flash("Solo agentes y administradores pueden ver estadísticas.")
        return redirect(url_for('index'))

    agente_filtro = request.args.get('agente_id', '').strip()
    filtro_agente_id = int(agente_filtro) if agente_filtro else None
    filtro_sql = ''
    filtro_params = ()
    if filtro_agente_id:
        filtro_sql = ' AND agente_id = %s'
        filtro_params = (filtro_agente_id,)

    def contar(sql, extra_params=()):
        micursor.execute(sql + filtro_sql, filtro_params + extra_params)
        return micursor.fetchone()['n']

    total = contar("SELECT COUNT(*) AS n FROM tickets WHERE 1=1")
    abiertos = contar("SELECT COUNT(*) AS n FROM tickets WHERE estado='Abierto'")
    proceso = contar("SELECT COUNT(*) AS n FROM tickets WHERE estado='En proceso'")
    cerrados = contar("SELECT COUNT(*) AS n FROM tickets WHERE estado='Cerrado'")
    alta_abiertos = contar(
        "SELECT COUNT(*) AS n FROM tickets WHERE prioridad='alta' AND estado != 'Cerrado'"
    )
    sin_asignar = contar(
        "SELECT COUNT(*) AS n FROM tickets WHERE agente_id IS NULL AND estado != 'Cerrado'"
    )
    cerrados_semana = contar("""
        SELECT COUNT(*) AS n FROM tickets
        WHERE estado='Cerrado' AND cerrado_en >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)

    micursor.execute("""
        SELECT a.nombre, COUNT(t.id) AS total
        FROM tickets t
        INNER JOIN usuarios a ON t.agente_id = a.id
        WHERE t.estado != 'Cerrado'
        """ + (filtro_sql.replace('agente_id', 't.agente_id') if filtro_sql else '') + """
        GROUP BY a.nombre
        ORDER BY total DESC
    """, filtro_params)
    por_agente = micursor.fetchall()

    sql_categoria = """
        SELECT cat.nombre, COUNT(t.id) AS total
        FROM tickets t
        LEFT JOIN categorias cat ON t.categoria_id = cat.id
        WHERE 1=1
    """
    if filtro_sql:
        sql_categoria += filtro_sql.replace('agente_id', 't.agente_id')
    sql_categoria += " GROUP BY cat.nombre ORDER BY total DESC"
    micursor.execute(sql_categoria, filtro_params)
    por_categoria = micursor.fetchall()

    sql_ultimos = "SELECT titulo, creado_en FROM tickets WHERE 1=1"
    sql_ultimos += filtro_sql + " ORDER BY creado_en DESC LIMIT 5"
    micursor.execute(sql_ultimos, filtro_params)
    ultimos = micursor.fetchall()

    sla_filtro = filtro_sql.replace('agente_id', 't.agente_id') if filtro_sql else ''
    sla_params = filtro_params

    micursor.execute("""
        SELECT COUNT(*) AS n FROM tickets t
        WHERE t.estado != 'Cerrado'
          AND t.primera_respuesta_en IS NULL
          AND t.sla_respuesta_limite IS NOT NULL
          AND NOW() > t.sla_respuesta_limite
    """ + sla_filtro, sla_params)
    sla_resp_vencidos = micursor.fetchone()['n']

    micursor.execute("""
        SELECT COUNT(*) AS n FROM tickets t
        WHERE t.estado != 'Cerrado'
          AND t.sla_resolucion_limite IS NOT NULL
          AND NOW() > t.sla_resolucion_limite
    """ + sla_filtro, sla_params)
    sla_resol_vencidos = micursor.fetchone()['n']

    micursor.execute("""
        SELECT COUNT(*) AS n FROM tickets t
        WHERE t.estado != 'Cerrado'
          AND t.sla_respuesta_limite IS NOT NULL
          AND t.primera_respuesta_en IS NULL
          AND NOW() < t.sla_respuesta_limite
          AND TIMESTAMPDIFF(SECOND, NOW(), t.sla_respuesta_limite)
              <= TIMESTAMPDIFF(SECOND, t.creado_en, t.sla_respuesta_limite) * 0.25
    """ + sla_filtro, sla_params)
    sla_en_riesgo = micursor.fetchone()['n']

    # Gráfico de barras: tickets por agente asignado (todos los estados)
    micursor.execute("""
        SELECT COALESCE(a.nombre, 'Sin asignar') AS nombre, COUNT(t.id) AS total
        FROM tickets t
        LEFT JOIN usuarios a ON t.agente_id = a.id
        GROUP BY t.agente_id, a.nombre
        ORDER BY total DESC
    """)
    chart_agentes = micursor.fetchall()
    agentes = [f['nombre'] for f in chart_agentes]
    tickets_por_agente = [f['total'] for f in chart_agentes]

    return render_template(
        'dashboard.html',
        total=total,
        abiertos=abiertos,
        proceso=proceso,
        cerrados=cerrados,
        alta_abiertos=alta_abiertos,
        sin_asignar=sin_asignar,
        cerrados_semana=cerrados_semana,
        por_agente=por_agente,
        por_categoria=por_categoria,
        ultimos=ultimos,
        sla_resp_vencidos=sla_resp_vencidos,
        sla_resol_vencidos=sla_resol_vencidos,
        sla_en_riesgo=sla_en_riesgo,
        agentes=agentes,
        tickets_por_agente=tickets_por_agente,
        lista_agentes=listar_agentes(),
        filtro_agente_id=filtro_agente_id,
    )


# Historial de correos enviados por el sistema (solo administrador).
@app.route('/notificaciones')
def historial_notificaciones():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    if session.get('usuario_rol') != 'admin':
        flash("Solo administradores pueden ver el historial de notificaciones.")
        return redirect(url_for('index'))

    filas = listar_notificaciones_db(micursor, 100)
    return render_template(
        'notificaciones.html',
        notificaciones=filas,
        mail_habilitado=config_mail.MAIL_ENABLED,
    )


def _leer_manual(nombre_archivo):
    ruta = os.path.join(os.path.dirname(__file__), nombre_archivo)
    if not os.path.isfile(ruta):
        return None
    with open(ruta, encoding='utf-8') as f:
        return f.read()


# Manual de usuario — documentación para clientes, agentes y administradores.
@app.route('/manual/usuario')
def manual_usuario():
    texto = _leer_manual('MANUAL_USUARIO.md')
    if texto is None:
        flash('No se encontró el manual de usuario.')
        return redirect(url_for('index') if session.get('usuario_id') else url_for('login'))
    return render_template(
        'manual_view.html',
        titulo='Manual de usuario',
        contenido_md=texto,
    )


# Manual técnico — arquitectura, base de datos y despliegue (evaluación).
@app.route('/manual/tecnico')
def manual_tecnico():
    texto = _leer_manual('MANUAL_TECNICO.md')
    if texto is None:
        flash('No se encontró el manual técnico.')
        return redirect(url_for('index') if session.get('usuario_id') else url_for('login'))
    return render_template(
        'manual_view.html',
        titulo='Manual técnico',
        contenido_md=texto,
    )


# Ejecución
if __name__ == "__main__":
    app.run(debug=True)
