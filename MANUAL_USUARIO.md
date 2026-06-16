# Manual de usuario — Galsoft Helpdesk

Sistema web de soporte técnico para gestionar peticiones (tickets) entre clientes, agentes y administradores.

**URL de acceso:** http://127.0.0.1:5000  

---

## 1. Roles del sistema

| Rol | Descripción |
|-----|-------------|
| **Cliente** | Abre peticiones, consulta sus tickets y comenta. |
| **Agente** | Ve todos los tickets, los asigna, responde, gestiona estado y prioridad. |
| **Administrador** | Todo lo del agente más usuarios, categorías, notificaciones y configuración global. |

---

## 2. Acceso al sistema

### 2.1 Iniciar sesión
1. Abra el navegador en la dirección del helpdesk.
2. Introduzca **correo** y **contraseña**.
3. Pulse **Entrar**.

Si los datos son correctos, entrará al listado de tickets.

### 2.2 Registrarse (solo clientes)
1. En la pantalla de login, pulse **Registrarse**.
2. Rellene **nombre**, **correo** y **contraseña** (mínimo 6 caracteres).
3. La cuenta se crea con rol **cliente** automáticamente.
4. Los roles **agente** y **admin** los asigna un administrador.

### 2.3 Recuperar contraseña olvidada

Si olvidó su contraseña y **no** puede iniciar sesión (requiere correo activo en `mail.env`):

1. En **Iniciar sesión**, pulse **¿Olvidaste tu contraseña?**
2. Introduzca su **correo electrónico** y pulse **Enviar enlace**.
3. Revise su bandeja (y carpeta spam): recibirá un correo de Galsoft Helpdesk con un **enlace**.
4. Abra el enlace (válido **24 horas**) y escriba la **contraseña nueva** dos veces.
5. Vuelva a **Iniciar sesión** con la nueva contraseña.

| Situación | Qué hacer |
|-----------|-----------|
| No llega el correo | Compruebe spam; verifique que el email es el de su cuenta; admin revisa **Notificaciones**. |
| El enlace caducó | Solicite uno nuevo en **¿Olvidaste tu contraseña?** |
| El correo no está activo | Contacte al **administrador** (Usuarios → Editar → nueva contraseña). |

### 2.4 Cambiar contraseña (con sesión iniciada)

1. Menú lateral → **Cambiar contraseña**.
2. Pulse **Enviar enlace a mi correo**.
3. Abra el enlace del correo y elija la nueva contraseña.

### 2.5 Cerrar sesión
- Barra superior: botón **Salir**, o menú lateral **Cerrar sesión**.

---

## 3. Navegación

### Menú lateral (☰)
- **Inicio** — Listado de tickets.
- **Nueva petición** — Crear ticket.
- **Tickets** (agente/admin):
  - **Todos** — Sin filtro de estado.
  - **Abiertos** / **En proceso** / **Cerrados** — Filtro rápido.
- **Estadísticas** — Panel de métricas (agente/admin).
- **Usuarios** — Gestión de cuentas (solo admin).
- **Categorías** — Tipos de ticket (solo admin).
- **Notificaciones** — Historial de correos enviados (solo admin).
- **Cambiar contraseña** — Envía enlace al correo del usuario logueado.

### Cabecera
- Logo Galsoft y nombre del usuario con su rol.
- Botón **Salir**.

---

## 4. Cliente — Guía paso a paso

### 4.1 Crear una petición
1. **Nueva petición**.
2. Rellene:
   - **Título** — Resumen breve del problema.
   - **Descripción** — Detalle de la incidencia.
   - **Categoría** — Tipo de consulta (Hardware, Software, etc.).
   - **Prioridad** — Baja, media o alta.
   - **Archivo** (opcional) — Adjunto (captura, documento).
3. Pulse crear/guardar.
4. Se abre el **detalle del ticket** recién creado.

### 4.2 Ver sus tickets
- En **Inicio** solo aparecen **sus** peticiones, en tarjetas (cuadrados).
- Cada tarjeta muestra: número, estado, prioridad, categoría, agente, fecha y SLA (si aplica).
- Pulse **Ver detalle** para entrar al ticket.

### 4.3 Comentar en un ticket
1. Entre en el detalle del ticket.
2. Escriba su mensaje en **Añadir comentario**.
3. Pulse **Enviar comentario**.

El cliente **no** puede crear notas internas. Solo ve comentarios públicos en el historial.

### 4.4 Descargar adjuntos
Si el ticket tiene archivo adjunto, use **Descargar adjunto** en la ficha de información.

---

## 5. Agente — Guía paso a paso

### 5.1 Listado y filtros
En **Inicio** ve **todos** los tickets. Puede filtrar por:
- Texto (título o descripción).
- Estado, prioridad, categoría.
- **Mis tickets** — Asignados a usted.
- **Sin asignar** — Pendientes de agente.

Pulse **Filtrar**. Si hay filtros activos, use **Ver todos** para quitarlos.

### 5.2 Tomar un ticket
1. Abra un ticket **sin asignar**.
2. Pulse **Tomar ticket (asignarme)**.
3. El sistema le asigna el ticket y, si estaba abierto, pasa a **En proceso**.

### 5.3 Gestionar un ticket
En el panel **Gestionar ticket** puede cambiar:
- **Estado** — Abierto, En proceso, Cerrado.
- **Prioridad** — Baja, media, alta.
- **Comentario** — Se guarda en el historial.

Opciones:
- **Nota interna** — Solo visible para agentes y administradores.
- Comentario público — El cliente lo ve y puede recibir correo (si el envío está activo).

### 5.4 Comentarios y notas internas
- **Comentario público** — Visible para el cliente; cuenta para SLA de primera respuesta.
- **Nota interna** — Marque la casilla correspondiente; el cliente no la verá.

### 5.5 Panel de estadísticas
Menú **Estadísticas**:
- Totales por estado (Abiertos, En proceso, Cerrados).
- Tickets sin asignar, prioridad alta, cerrados en 7 días.
- SLA vencido y en riesgo.
- Tablas por agente y por categoría.
- Gráfico de distribución por estado.

---

## 6. Administrador — Funciones adicionales

### 6.1 Gestión de usuarios
1. Menú **Usuarios**.
2. Busque por nombre o correo (opcional).
3. Pulse **Editar** en un usuario.
4. Puede cambiar nombre, correo, **rol** (cliente / agente / admin) y **contraseña**.
5. También puede pulsar **Eliminar** (en listado o edición), confirmar y borrar el usuario.

Para **restablecer la contraseña** de un usuario:
1. **Usuarios → Editar** en ese usuario.
2. Escriba una **nueva contraseña** en el campo correspondiente (dejar vacío = no cambia).
3. **Guardar cambios**.
4. Comunique la contraseña temporal al usuario por un canal seguro (teléfono, en persona, etc.).

Al eliminar, el sistema pide confirmación. No se puede deshacer.

**Importante:** El correo del cliente debe ser válido para notificaciones de tickets y para **recuperar/cambiar contraseña** por enlace.

### 6.2 Categorías
1. Menú **Categorías**.
2. Escriba el nombre y pulse **Añadir**.
3. Las categorías aparecen al crear tickets y en los filtros.

### 6.3 Notificaciones por correo
Menú **Notificaciones** — Historial de envíos:
- Fecha, tipo, destinatario, asunto, ticket y si se **envió** o **no**.

Requiere archivo `mail.env` configurado en el servidor (SMTP IONOS u otro).

### 6.4 Asignar agente manualmente
En el detalle del ticket, el admin puede elegir **Agente asignado** en el formulario de gestión.

---

## 7. Estados, prioridades y colores

### Estados del ticket
| Estado | Color | Significado |
|--------|-------|-------------|
| <span class="estado-abierto">Abierto</span> | <span class="estado-abierto">Verde</span> | Petición nueva o pendiente de tramitar. |
| <span class="estado-proceso">En proceso</span> | <span class="estado-proceso">Amarillo</span> | Un agente está trabajando en ella. |
| <span class="estado-cerrado">Cerrado</span> | <span class="estado-cerrado">Rojo</span> | Resuelta o finalizada. |

### Prioridad
| Prioridad | Color |
|-----------|-------|
| <span class="prioridad-baja">Baja</span> | <span class="prioridad-baja">Verde</span> |
| <span class="prioridad-media">Media</span> | <span class="prioridad-media">Amarillo</span> |
| <span class="prioridad-alta">Alta</span> | <span class="prioridad-alta">Rojo</span> |

### SLA (niveles de servicio)
Plazos desde la creación del ticket:

| Prioridad | 1ª respuesta | Resolución (cierre) |
|-----------|--------------|---------------------|
| Alta | 4 horas | 24 horas |
| Media | 8 horas | 48 horas |
| Baja | 24 horas | 72 horas |

**Indicadores SLA:**
| Indicador | Color | Significado |
|-----------|-------|-------------|
| En plazo / Cumplido | <span class="sla-cumplido">Verde</span> | Dentro del plazo o respondido/cerrado a tiempo. |
| En riesgo | <span class="sla-riesgo">Amarillo</span> | Queda poco margen (último 25 % del plazo). |
| Vencido | <span class="sla-vencido">Rojo</span> | Se ha superado el plazo. |

La **primera respuesta** cuenta cuando un agente o admin deja un **comentario público** (las notas internas no cuentan).

---

## 8. Notificaciones por correo

El sistema puede enviar correos automáticos (si `MAIL_ENABLED=1` en `mail.env`):

| Evento | Quién recibe el correo |
|--------|------------------------|
| Ticket nuevo | Cliente + equipo de soporte |
| Comentario del cliente | Agente asignado (o todo el equipo) |
| Comentario del agente (público) | Cliente |
| Cambio de estado | Cliente |
| Asignación de ticket | Agente asignado |

Si el correo no está configurado, la aplicación funciona igual; los avisos quedan registrados en **Notificaciones**.

---

## 9. Historial de actividad

En el detalle de cada ticket, el **historial** registra:
- Creación del ticket.
- Cambios de estado y prioridad.
- Asignaciones de agente.
- Comentarios públicos.
- Notas internas (solo agente/admin).
- Archivos adjuntos.

Las fechas se muestran en formato **DD-MM-AAAA HH:MM**.

---

## 10. Preguntas frecuentes

**¿Por qué no veo todos los tickets?**  
Si es **cliente**, solo ve los suyos. Agentes y administradores ven todos.

**¿Por qué el cliente no recibe correos?**  
Compruebe que tiene email en su ficha, que el comentario no es nota interna y que `mail.env` está activo. Revise **Notificaciones** (admin). Los correos de tickets son independientes de recuperar la contraseña.

**¿Olvidé mi contraseña?**  
Use **¿Olvidaste tu contraseña?** en el login. Recibirá un **correo con enlace** (24 h). Con sesión iniciada también puede usar menú **Cambiar contraseña**.

**¿Por qué no llega el correo de recuperación?**  
Compruebe `MAIL_ENABLED=1` en `mail.env`, spam, y que el email de la cuenta sea correcto. El admin ve el detalle en **Notificaciones**.

**¿Qué es una nota interna?**  
Mensaje solo para el equipo de soporte; el cliente no lo ve ni recibe aviso.

**¿Por qué debo iniciar sesión otra vez al reiniciar el servidor?**  
Es normal con `app.secret_key = os.urandom(24)`: la clave de sesión cambia en cada arranque.

**¿No carga la página (error de conexión)?**  
Compruebe que MySQL está activo, que importó **`helpdesk.sql`** y que ejecutó `python app.py` en la carpeta del proyecto.

**¿Cómo instalo la base de datos la primera vez?**  
En phpMyAdmin: **Importar** → elegir **`helpdesk.sql`** → Continuar. Eso crea la base `helpdesk` con usuarios, categorías y tickets de prueba.

---

## 11. Contacto y soporte del sistema

Para incidencias del propio helpdesk (accesos, roles, correo corporativo), contacte con el **administrador** de Galsoft.

---

**Ver en la aplicación:** http://127.0.0.1:5000/manual/usuario (también desde el pie de página).

---

*Galsoft Helpdesk — Manual de usuario*
