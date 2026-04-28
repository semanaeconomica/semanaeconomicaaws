# se_async_export — Explicación del código

Módulo Odoo 13 que resuelve los cortes del navegador al exportar xlsx grandes
desde la UI. Pensado específicamente para el CRM de Semana Económica, pero
funciona en cualquier modelo del sistema.

---

## 1. Qué problema resuelve

Cuando un usuario da click a **Exportar → XLSX** en una vista de lista con
muchos registros (ej. 114,469 oportunidades con "paywa" en el nombre), el
navegador muestra:

> Something happened trying to contact the server, check that the server is online...

El mensaje NO viene de un error del servidor. Viene del handler
`xhr.onerror` en `odoo/addons/web/static/src/js/core/ajax.js:312`, que se
dispara cuando la petición HTTP no se completa a nivel de red.

### Por qué se corta

El endpoint nativo `/web/export/xlsx`:

1. Lee los 114k registros con `search_read`.
2. Arma el xlsx **completo en RAM** usando `xlsxwriter`.
3. Recién al terminar (~110 s) devuelve los bytes en la respuesta HTTP.

Durante esos ~110 s el servidor **no envía ni un byte** al navegador.
Cualquier firewall/VPN/proxy corporativo con idle-timeout < 110 s (muy común:
Palo Alto, Fortinet, ZScaler, Cisco suelen tener 60–120 s) considera la
conexión muerta y la cierra.

El backup de Odoo (que aguanta 40+ min) no sufre este problema porque usa
`werkzeug.wrappers.Response(stream, direct_passthrough=True)` — envía bytes
mientras `pg_dump` los genera. Hay tráfico continuo → firewall nunca corta.

### La solución de este módulo

Desacoplar el "generar xlsx" del "descargar xlsx":

1. El click dispara una petición rápida (<1 s) que **crea un job** y lanza
   un thread en el servidor.
2. El navegador abre un modal con barra de progreso y hace **polling cada 3 s**
   al endpoint `/se_export/status`. Cada poll es tráfico HTTP → firewall
   nunca ve la conexión idle.
3. Cuando el job termina, el servidor ya tiene el xlsx guardado como
   `ir.attachment`. El modal detecta `state='done'` en el próximo poll y
   dispara la descarga de un archivo **ya generado**, que baja en segundos.

Para el usuario: **un solo click, archivo descarga**. Igual que antes, pero
sin el corte.

---

## 2. Arquitectura de alto nivel

```
┌──────────────┐         ┌─────────────────┐         ┌──────────────┐
│  Navegador   │         │  Odoo Worker    │         │  Thread      │
│  (usuario)   │         │  (HTTP)         │         │  (background)│
└──────┬───────┘         └────────┬────────┘         └──────┬───────┘
       │                          │                         │
       │ click Exportar XLSX      │                         │
       │ (DataExport dialog)      │                         │
       │                          │                         │
       │ POST /se_export/start    │                         │
       ├─────────────────────────►│                         │
       │                          │ create job (state=pending)
       │                          │ cr.commit()             │
       │                          │ threading.Thread.start()├─────► _run()
       │                          │                         │      state=running
       │◄─ {job_id: 42} ──────────┤                         │      generar xlsx
       │                          │                         │        (xlsxwriter
       │ cerrar DataExport        │                         │         constant_memory)
       │ abrir ProgressDialog     │                         │        progress updates
       │                          │                         │         via cursor
       │ [POLL cada 3s]           │                         │         separado
       │ POST /se_export/status   │                         │
       ├─────────────────────────►│                         │
       │ ◄─{progress:23,running}──┤                         │
       │                          │                         │
       │ POST /se_export/status   │                         │
       ├─────────────────────────►│                         │
       │ ◄─{progress:67,running}──┤                         │
       │                          │                         │      crear ir.attachment
       │                          │                         │      state=done
       │                          │                         │      bus.sendone()
       │                          │                         │◄─────
       │ POST /se_export/status   │                         │
       ├─────────────────────────►│                         │
       │ ◄─{done, url:/web/...}───┤                         │
       │                          │                         │
       │ <a href=url download>    │                         │
       │ GET /web/content/88      │                         │
       ├─────────────────────────►│                         │
       │ ◄── xlsx bytes ──────────┤                         │
       │ (archivo YA generado)    │                         │
       │ cierra modal             │                         │
```

---

## 3. Estructura del módulo

```
se_async_export/
├── __manifest__.py                         # metadatos + data files
├── __init__.py                             # importa models + controllers
│
├── models/
│   ├── __init__.py
│   └── export_xlsx_job.py                  # modelo export.xlsx.job (núcleo)
│
├── controllers/
│   ├── __init__.py
│   └── main.py                             # endpoints /start y /status
│
├── data/
│   └── ir_cron_data.xml                    # cron que marca huérfanos
│
├── security/
│   ├── ir.model.access.csv                 # ACL CRUD a group_user
│   └── export_xlsx_job_rules.xml           # record rule: solo ves tus jobs
│
├── views/
│   ├── assets.xml                          # carga el JS en el bundle backend
│   └── export_job_views.xml                # tree + form + menú "Mis exportaciones"
│
└── static/src/
    ├── js/async_export.js                  # ProgressDialog + include DataExport
    └── xml/async_export.xml                # QWeb template del modal
```

---

## 4. Archivo por archivo

### 4.1. `__manifest__.py`

Declara el módulo a Odoo. Puntos importantes:

- `'version': '13.0.1.0.0'` — convención Odoo: primer par es la serie
  (13.0), los siguientes tres son mayor.menor.patch del módulo.
- `'depends': ['web', 'mail', 'bus']` — necesitamos `web` por el
  `DataExport` a intervenir; `mail` y `bus` para notificaciones futuras.
- `'data': [...]` — lista de XML/CSV a cargar en orden. El orden importa
  porque los XML pueden referenciar `xml_id` declarados en archivos previos.
- `'qweb': ['static/src/xml/async_export.xml']` — los templates QWeb
  cliente se declaran aparte del `data`. En Odoo 13 esto es obligatorio
  (en 14+ se unifica con assets).
- `'installable': True, 'application': False` — módulo instalable pero no
  aparece como "aplicación" en el filtro de Apps.

### 4.2. `__init__.py`

```python
from . import models
from . import controllers
```

Carga los submódulos Python. `models` y `controllers` son paquetes con su
propio `__init__.py` que a su vez importan los archivos concretos.

### 4.3. `models/export_xlsx_job.py` (el corazón)

Modelo `export.xlsx.job` que representa cada pedido de exportación.

#### Campos

| Campo | Tipo | Rol |
|---|---|---|
| `name` | Char | Nombre visible ("Export crm.lead (114469)") |
| `model_name` | Char | Modelo técnico a exportar ('crm.lead') |
| `domain` | Text | Dominio serializado en JSON |
| `fields_json` | Text | Lista de campos `[{name, label}, ...]` en JSON |
| `user_id` | M2O(res.users) | Dueño del job (usado por record rule) |
| `state` | Selection | pending / running / done / failed |
| `progress` | Integer | 0–100. Actualizado durante la generación |
| `total_rows` | Integer | Total de registros del dominio |
| `attachment_id` | M2O(ir.attachment) | El xlsx generado, link de descarga |
| `error_msg` | Text | Si `failed`, el mensaje |
| `started_at`, `finished_at` | Datetime | Timestamps |

#### Métodos clave

**`create_job(model_name, domain, fields_list, name=None)`** — `@api.model`

Entry point público. Lo llama el controller `/start`. Qué hace:

1. `Model.check_access_rights('read')` — valida que el user puede leer ese modelo.
2. `search_count(domain)` — cuenta los registros para mostrar total en el modal.
3. `self.create({...})` — graba el job con `state='pending'`.
4. **`self.env.cr.commit()`** — crítico: el thread va a abrir un cursor nuevo
   y necesita ver este job ya commiteado en la BD.
5. `threading.Thread(target=self._run_in_thread, ...).start()` — dispara
   el worker en un thread separado y retorna.

**`_run_in_thread(dbname, uid, job_id)`** — `@staticmethod`

Entry point del thread. Es estático porque se ejecuta fuera del contexto
del request HTTP. Qué hace:

```python
with registry(dbname).cursor() as cr:
    env = api.Environment(cr, uid, {})
    env['export.xlsx.job'].browse(job_id)._run()
```

- Abre un cursor **nuevo** desde el pool de conexiones (`registry(dbname).cursor()`).
- Construye un `api.Environment` con el uid del creador.
- El context manager (`with ...`) hace commit automático al salir sin
  excepciones, y close siempre.
- Si el thread explota con excepción no capturada, el `try/except` del
  entry point lo loguea pero no tumba el proceso.

**`_run()`**

Orquesta el ciclo de vida del job:

```
write(state=running, started_at=now) → cr.commit()
try:
    xlsx_bytes = _generate_xlsx()
    attachment = ir.attachment.create(datas=b64(bytes), ...)
    write(state=done, progress=100, attachment_id=X, finished_at=now)
    cr.commit()
except Exception as exc:
    cr.rollback()
    write(state=failed, error_msg=str(exc), finished_at=now)
    cr.commit()
finally:
    _notify_user()
```

Detalles:

- El primer `cr.commit()` publica `state=running` para que el polling lo vea.
- Si falla, hago `cr.rollback()` **antes** del `write(failed)`. Sin el
  rollback, la excepción previa dejó la transacción en estado ABORTED y
  cualquier `write` fallaría con `InFailedSqlTransaction`.
- `finally: _notify_user()` — notifica éxito o fracaso.

**`_generate_xlsx()`**

Genera el archivo. Lo más importante:

```python
book = xlsxwriter.Workbook(buf, {'constant_memory': True, 'in_memory': True})
```

- `constant_memory=True` — xlsxwriter escribe al buffer por fila y libera
  memoria. Sin esto, las 114k filas se acumulan en RAM → riesgo de OOM.
- `in_memory=True` — todo el zip xlsx vive en un `BytesIO` (no toca disco).

Después itera en batches de 1000 vía `search_read`:

```python
while True:
    batch = Model.search_read(domain, field_names,
                              offset=offset, limit=1000, order='id')
    if not batch: break
    for rec in batch:
        for col, fname in enumerate(field_names):
            sheet.write(row_idx, col, self._cell_value(rec.get(fname)))
        row_idx += 1
        rows_since_progress += 1
        if rows_since_progress >= 500:
            pct = min(99, int((row_idx-1) * 100 / total))
            self._update_progress(pct)   # cursor SEPARADO
            rows_since_progress = 0
    offset += 1000
```

- `order='id'` asegura paginación estable (sin el order, offset/limit sin
  orden es no-determinista en PG).
- `_cell_value()` normaliza tipos: tuplas `[id, display_name]` de m2o
  → `display_name`; `False` → `''`; listas (x2m) → csv.

**`_update_progress(pct)`** — truco importante

```python
with registry(self.env.cr.dbname).cursor() as cr:
    cr.execute("UPDATE export_xlsx_job SET progress = %s WHERE id = %s",
               (pct, self.id))
```

Usa un cursor **aparte** del thread principal. ¿Por qué?

Si escribiera `self.progress = pct` en el cursor del thread, el valor
viviría en esa transacción hasta el commit final. El endpoint `/status`
(que corre en OTRO cursor en OTRO worker) no lo vería hasta terminar
todo.

Al abrir un cursor propio y dejar que el `with` lo commitee, **el UPDATE
se publica inmediatamente** → el polling lo lee. Sí, se pierde la
atomicidad del progress, pero para este campo da igual: es aprox, no
financiero.

**`_notify_user()`**

```python
channel = (self.env.cr.dbname, 'res.partner', self.user_id.partner_id.id)
self.env['bus.bus'].sendone(channel, payload)
```

Patrón verificado contra `odoo/addons/mail/models/mail_message.py`:
el canal bus.bus canónico para notificar a un usuario es
`(dbname, 'res.partner', partner_id)` — NO `('res.users', user_id)`.

El JS no está usando bus todavía (solo polling), pero dejo esto listo por
si queremos agregar push en el futuro.

**`_cron_mark_orphans()`** — `@api.model`

Si un thread muere a mitad del `_generate_xlsx` (OOM, reinicio de Odoo),
el job queda para siempre en `state='running'`. Este cron se ejecuta
cada 5 min (definido en `data/ir_cron_data.xml`) y marca como `failed`
cualquier job `running` desde hace más de 20 minutos.

### 4.4. `controllers/main.py`

Dos endpoints JSON-RPC (`type='json'`):

**`POST /se_export/start`**

```python
@http.route('/se_export/start', type='json', auth='user')
def start(self, model, domain, fields, name=None):
    # validaciones
    job = request.env['export.xlsx.job'].create_job(...)
    return {'job_id': job.id, 'total_rows': job.total_rows}
```

- `type='json'` — usa JSON-RPC, mismo formato que Odoo usa internamente.
  Los params llegan como kwargs.
- `auth='user'` — requiere sesión. Odoo devuelve 401 si no hay.
- Delega la lógica al modelo. El controller solo hace validación de
  entrada y serialización de salida.

**`POST /se_export/status`**

```python
@http.route('/se_export/status', type='json', auth='user')
def status(self, job_id):
    job = request.env['export.xlsx.job'].browse(int(job_id))
    if not job.exists():
        raise AccessError(...)
    url = False
    if job.state == 'done' and job.attachment_id:
        url = '/web/content/%d?download=true' % job.attachment_id.id
    return {'state': ..., 'progress': ..., 'attachment_url': url, ...}
```

Punto de seguridad: `job.exists()` en vez de chequear `job.user_id == user`
manualmente. La record rule en `export_xlsx_job_rules.xml` filtra al ORM
de modo que `browse(id_ajeno).exists()` retorna recordset vacío. Así si
un user A adivina el `job_id` de un user B, le llega `AccessError` limpio.

### 4.5. `data/ir_cron_data.xml`

Registra el cron en la BD cuando se instala el módulo:

```xml
<record id="ir_cron_mark_orphan_jobs" model="ir.cron">
    <field name="name">Async Export: marcar jobs huérfanos</field>
    <field name="model_id" ref="model_export_xlsx_job"/>
    <field name="state">code</field>
    <field name="code">model._cron_mark_orphans()</field>
    <field name="user_id" ref="base.user_root"/>
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
    <field name="numbercall">-1</field>
</record>
```

- `noupdate="1"` en el `<data>` wrapping: al actualizar el módulo no
  se pisa lo que el admin haya editado en Ajustes.
- `model_export_xlsx_job` es un xml_id autogenerado por Odoo (prefijo
  `model_` + nombre técnico con `.` → `_`).
- `code: model._cron_mark_orphans()` — `model` es la variable implícita
  que Odoo pasa al cron: `self.env[cron.model_id.model]`.
- `numbercall=-1` → infinito.

### 4.6. `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_export_xlsx_job_user,export.xlsx.job.user,model_export_xlsx_job,base.group_user,1,1,1,1
```

ACL a nivel modelo: cualquier user interno (`base.group_user`) tiene CRUD.
**Sola esta ACL sería insegura**: cualquier user vería jobs de cualquier
otro. Por eso agregamos una record rule.

### 4.7. `security/export_xlsx_job_rules.xml`

```xml
<record id="export_xlsx_job_own_rule" model="ir.rule">
    <field name="domain_force">[('user_id','=',user.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
</record>
```

Record rule: filtra el recordset del ORM según dominio. Para group_user:
solo los jobs propios.

Nota: el superuser (admin, id=1) saltea TODAS las record rules. Por eso
admin ve todos los jobs en el menú "Mis exportaciones". Comportamiento
estándar de Odoo.

### 4.8. `views/assets.xml`

```xml
<template id="assets_backend" name="..." inherit_id="web.assets_backend">
    <xpath expr="." position="inside">
        <script type="text/javascript"
                src="/se_async_export/static/src/js/async_export.js"/>
    </xpath>
</template>
```

En Odoo 13 los assets se declaran heredando el template
`web.assets_backend` (el bundle del backend). `xpath="." position="inside"`
agrega al final del bundle. Esto es JS vanilla, Odoo no hace bundling/
minificación como webpack — concatena y sirve.

### 4.9. `views/export_job_views.xml`

Define las vistas Odoo estándar:

- `view_export_xlsx_job_tree` — vista lista con `progress` como
  `widget="progressbar"` (barra visual nativa).
- `view_export_xlsx_job_form` — vista detalle. `error_msg` se esconde
  con `attrs="{'invisible': [('state','!=','failed')]}"` si no falló.
- `action_export_xlsx_job` — action con `domain=[('user_id','=',uid)]`
  (además de la record rule, por cosmética).
- `menuitem` bajo `base.menu_administration` con label "Mis exportaciones".

### 4.10. `static/src/js/async_export.js` (la lógica del cliente)

Dos piezas dentro de un mismo `odoo.define('se_async_export.AsyncExport', ...)`:

#### 4.10.1. `ProgressDialog`

Extiende `web.Dialog`. El único estado interno: `jobId`, `totalRows`,
`progress`, `_destroyed`, `_pollHandle`.

Ciclo:

1. `init` → configura título y pasa `buttons: []` (sin footer).
2. `start` → renderiza el body (template QWeb) y llama `_schedulePoll()`.
3. `_schedulePoll` → `setTimeout(_poll, 3000)`. Guarda el handle para
   poder cancelar en `destroy`.
4. `_poll` → `this._rpc({route: '/se_export/status', params: {...}})`.
   - On success → `_onStatus(result)`.
   - On error (red) → `_schedulePoll()` (reintenta, no rompe el modal).
5. `_onStatus`:
   - `done` → `_triggerDownload(url)` + `this.close()`.
   - `failed` → `close()` + `Dialog.alert(msg)`.
   - `running`/`pending` → `_updateProgress()` + `_schedulePoll()`.
6. `destroy` → setea `_destroyed=true` y `clearTimeout`. Sin esto, si el
   user cierra el modal queda un poll fantasma disparándose.

El download se dispara con un `<a href download>` sintético en vez de
`window.location = url`. Ventaja: no navega fuera de Odoo ni dispara el
"Leaving page?" prompt del navegador.

#### 4.10.2. `DataExport.include({_exportData: ...})`

`include()` es el mecanismo Odoo para hacer **override** de un widget
existente. Los métodos de dentro se mergean en el prototype.

```javascript
_exportData: function (exportedFields, exportFormat, idsToExport) {
    var _super = this._super.bind(this);
    var args = arguments;

    if (exportFormat !== 'xlsx' || idsToExport) {
        return _super.apply(this, args);
    }
    // ... decisión asíncrona
}
```

Detalle crítico: **capturar `_super.bind(this)` ANTES** de entrar a
cualquier `.then()`. Dentro del callback de una promesa, `this._super`
apunta a otra cosa (o a nada) y la llamada falla.

Lógica:

- Si el formato es CSV o si el user marcó filas específicas (`idsToExport`
  truthy) → flujo nativo. No nos metemos.
- Si es xlsx con dominio completo → `search_count` para saber cuántos son.
- `count < 5000` → nativo (no vale la pena la infra async).
- `count >= 5000` → `_runAsyncExport`:
  1. `blockUI()` spinner.
  2. POST `/se_export/start` con el payload completo.
  3. `unblockUI()`, `this.close()` (cierra DataExport).
  4. `new ProgressDialog(parent, {...}).open()`.

### 4.11. `static/src/xml/async_export.xml`

Template QWeb del modal. Notar que **no** empieza con `<div class="modal-dialog">`
— eso ya lo pone `web.Dialog` envolviendo nuestro contenido. Nuestro
template es solo el **body** del modal.

Usa Bootstrap 4 classes: `progress`, `progress-bar`, `progress-bar-striped`,
`progress-bar-animated`. El JS hace `$('.progress-bar').css('width', ...)`
para animar.

---

## 5. Decisiones técnicas relevantes

### 5.1. ¿Por qué threading y no cron?

Alternativas:

- **Cron cada 1 min que levanta jobs pending** — robusto, se reaprovecha
  de la infra Odoo de reintentos, jobs huérfanos tras reinicio se
  recuperan solos. Pero **agrega hasta 60 s de delay** antes de que
  arranque el job → UX empeora.
- **Threading** — inmediato. Pero si Odoo reinicia a mitad del job, el
  thread muere y el job queda running para siempre.

Elegí **threading + cron de respaldo**: UX inmediata, y el cron
`_cron_mark_orphans` limpia jobs huérfanos cada 5 min.

### 5.2. ¿Por qué no usar `queue_job` de OCA?

`queue_job` es un módulo OCA (Odoo Community Association) que implementa
una cola de trabajos robusta con priorización, reintentos, canales
separados, etc. Es la herramienta correcta para ambientes de producción
con alta concurrencia.

No lo uso porque:
- Agrega una dependencia externa (instalable pero más superficie).
- Para un solo caso de uso (export xlsx), es overkill.
- El servidor ya tiene 503 addons custom, no queremos agregar más
  deuda en el path de instalación.

Si en el futuro aparecen más casos de trabajos en background (ej.
integraciones, cálculos masivos), vale la pena migrar a `queue_job`.

### 5.3. ¿Por qué `constant_memory=True` en xlsxwriter?

Con `constant_memory=False` (default), xlsxwriter mantiene todo el xlsx
en RAM hasta `workbook.close()`. Para 114k filas × N columnas eso puede
ser 1–2 GB. Con 4 workers concurrentes haciendo exports grandes, el
servidor se queda sin RAM rápido.

Con `constant_memory=True` xlsxwriter escribe al buffer por fila y
libera. Trade-off: no podés volver a escribir celdas ya "salidas"
(ej. cambiar un formato). Para nuestro caso no lo necesitamos.

### 5.4. ¿Por qué umbral 5000?

Con ~110 s para 114k filas, la proyección es ~1 s por cada 1000 filas.
5000 filas ≈ 5–7 s de generación, claramente bajo cualquier idle timeout
razonable.

Es un número arbitrario, ajustable en `async_export.js` constante
`ASYNC_THRESHOLD`. Podría en el futuro leerse de un `ir.config_parameter`
para ajuste en runtime sin redeploy.

### 5.5. ¿Por qué polling y no solo bus.bus?

El bus.bus de Odoo 13 da notificaciones push al navegador vía longpolling.
Podríamos eliminar el `setTimeout` y esperar el mensaje del bus.

Dos razones para preferir polling:

1. **Robustez**: si el longpolling se cae (reconexión, worker de longpolling
   muerto), el polling HTTP directo sigue funcionando.
2. **Progress updates frecuentes**: el bus manda solo el evento final
   (done/failed). El polling ve `progress=23, 67, 100` durante la
   generación, llenando la barra en vivo. Para mandar progress via bus
   tendríamos que emitir mensajes cada X filas, saturando el canal.

El `_notify_user()` del modelo emite al bus como **nice-to-have** pero el
JS no lo consume hoy. Si se necesita reducir latencia entre "job done" y
"modal se cierra", agregar un listener del bus es de 10 líneas extra.

### 5.6. ¿Por qué no reescribir el xlsx endpoint para streaming?

Se pensó. Problema: el formato xlsx es un ZIP. El "central directory"
(tabla de contenidos del ZIP) se escribe al FINAL del archivo y contiene
offsets absolutos de los archivos internos. Hasta que xlsxwriter no
cierra el workbook, no hay forma de mandar bytes válidos.

Se podría mandar "bytes basura" de padding al inicio para mantener viva
la conexión, pero eso corrompe el xlsx desde el punto de vista del
navegador (los bytes van al file de descarga).

La solución real es: **desacoplar generación de descarga**. Es
exactamente lo que hace este módulo.

---

## 6. Cómo instalar y probar

### 6.1. Subir al servidor

```bash
# Desde local:
scp -i LLaveSemanaEconomica.pem -r se_async_export \
    ubuntu@3.235.180.230:/tmp/

# En el servidor:
sudo mv /tmp/se_async_export /opt/odoo/semanaeconomicaaws/
sudo chown -R odoo13_37:odoo /opt/odoo/semanaeconomicaaws/se_async_export
```

### 6.2. Actualizar la lista de módulos y activar

En la instancia de pruebas (`:8099`, BD `test_*`):

1. Apps → Actualizar Lista de Aplicaciones.
2. Quitar filtro "Aplicaciones", buscar "Async Export".
3. Instalar.

(O por línea de comandos:
`sudo systemctl restart odoo13_38 && sudo -u odoo13_37 /python-venv/3.7/odoo13/bin/python /opt/odoo/odoo13/odoo-bin -c /home/odoo13_37/odoo13_38.conf -u se_async_export --stop-after-init`)

### 6.3. Smoke test

- Ajustes → Técnico → Automatización → Programaciones → debe aparecer
  "Async Export: marcar jobs huérfanos".
- Menú superior → "Mis exportaciones" (bajo Ajustes) → vista vacía.
- No debe haber errores en `/var/log/odoo/odoo_test.log` al arrancar.

### 6.4. Test funcional

1. Ir a CRM → Pipeline.
2. Quitar filtro "Asignado a mí", agregar filtro "Oportunidad contiene paywa".
3. Seleccionar todos → Acción → Exportar.
4. Elegir formato XLSX, campos deseados → Exportar.
5. Debe aparecer el modal de progreso (no el error `xhr.onerror`).
6. Al terminar (~2 min), el archivo se descarga automáticamente.
7. Verificar en "Mis exportaciones" que el job quedó en state=done con
   attachment asociado.

---

## 7. Puntos abiertos / mejoras futuras

- **Cancel desde el modal**: hoy el user no puede cancelar un job en curso.
  Agregar botón "Cancelar" en el modal + endpoint `/se_export/cancel`.
- **Notificación bus.bus**: suscribir el JS al canal de partner para
  cerrar el modal instantáneamente al `done` (hoy tiene hasta 3 s de
  delay por el polling).
- **Limpieza automática**: jobs `done` con attachments viejos (>30 días)
  deberían auto-borrarse con otro cron.
- **Config parameter**: mover `ASYNC_THRESHOLD` de hardcoded a
  `ir.config_parameter`.
- **Observabilidad**: enviar métricas a un log estructurado (tiempo de
  generación, count, user, modelo) para detectar problemas de performance.
