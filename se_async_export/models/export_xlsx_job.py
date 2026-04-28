# -*- coding: utf-8 -*-
import base64
import io
import json
import logging
import threading
from datetime import timedelta

import xlsxwriter

from odoo import _, api, fields, models, registry

_logger = logging.getLogger(__name__)

BATCH_SIZE = 1000             # filas por search_read
PROGRESS_EVERY = 500          # actualizar progress cada N filas escritas
ORPHAN_MINUTES = 20           # jobs running > esto se marcan failed


class ExportXlsxJob(models.Model):
    _name = 'export.xlsx.job'
    _description = 'Asynchronous XLSX Export Job'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    model_name = fields.Char(required=True, index=True)
    domain = fields.Text(default='[]')
    fields_json = fields.Text(required=True)
    user_id = fields.Many2one(
        'res.users', required=True, ondelete='cascade',
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('running', 'Procesando'),
            ('done', 'Listo'),
            ('failed', 'Con error'),
        ],
        default='pending', required=True, index=True,
    )
    progress = fields.Integer(default=0)
    total_rows = fields.Integer(default=0)
    attachment_id = fields.Many2one('ir.attachment', ondelete='set null')
    error_msg = fields.Text()
    started_at = fields.Datetime()
    finished_at = fields.Datetime()

    # ------------------------------------------------------------------
    # API pública (la usa el controller /se_export/start)
    # ------------------------------------------------------------------
    @api.model
    def create_job(self, model_name, domain, fields_list, name=None):
        """Crea un job, lo commitea, y arranca un thread que lo ejecuta.

        :param model_name: str, nombre técnico (ej. 'crm.lead')
        :param domain: list de tuplas/listas (dominio Odoo)
        :param fields_list: list de dicts [{'name': 'id', 'label': 'ID'}, ...]
        :param name: str opcional, nombre visible del job
        :return: record export.xlsx.job
        """
        Model = self.env[model_name]
        Model.check_access_rights('read')

        total = Model.search_count(domain)

        job = self.create({
            'name': name or (_("Export %s") % model_name),
            'model_name': model_name,
            'domain': json.dumps(domain),
            'fields_json': json.dumps(fields_list),
            'total_rows': total,
        })

        # Commit obligatorio: el thread usa su propio cursor y debe ver el job.
        self.env.cr.commit()

        threading.Thread(
            target=self._run_in_thread,
            args=(self.env.cr.dbname, self.env.uid, job.id),
            name='se_async_export-%d' % job.id,
        ).start()

        return job

    # ------------------------------------------------------------------
    # Worker (se ejecuta dentro de un thread separado, cursor propio)
    # ------------------------------------------------------------------
    @staticmethod
    def _run_in_thread(dbname, uid, job_id):
        """Entry point del thread. Crea un environment nuevo y llama a _run.

        En Odoo 13 los threads externos al pool de workers deben envolver
        el uso de api.Environment con Environment.manage() para inicializar
        el stack envs en threading.local(). Sin eso el Environment.__new__
        falla con 'tuple object has no attribute cache'.
        """
        try:
            with api.Environment.manage():
                with registry(dbname).cursor() as cr:
                    env = api.Environment(cr, uid, {})
                    env['export.xlsx.job'].browse(job_id)._run()
        except Exception:
            _logger.exception("Thread del export job %s abortó", job_id)

    def _run(self):
        self.ensure_one()
        self.write({
            'state': 'running',
            'started_at': fields.Datetime.now(),
        })
        self.env.cr.commit()

        try:
            xlsx_bytes = self._generate_xlsx()
            # commit final de _generate_xlsx: refresca snapshot para que el
            # siguiente write no choque con progress updates commiteados.
            self.env.cr.commit()
            attachment = self.env['ir.attachment'].create({
                'name': '%s.xlsx' % self.name,
                'type': 'binary',
                'datas': base64.b64encode(xlsx_bytes),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype':
                    'application/vnd.openxmlformats-officedocument'
                    '.spreadsheetml.sheet',
            })
            self.env.cr.commit()
            self.write({
                'state': 'done',
                'progress': 100,
                'attachment_id': attachment.id,
                'finished_at': fields.Datetime.now(),
            })
            self.env.cr.commit()
        except Exception as exc:
            _logger.exception("Export job %s falló", self.id)
            self.env.cr.rollback()
            # escribir el failure en transacción limpia
            self.write({
                'state': 'failed',
                'error_msg': str(exc)[:2000],
                'finished_at': fields.Datetime.now(),
            })
            self.env.cr.commit()
        finally:
            self._notify_user()

    # ------------------------------------------------------------------
    # Generación del xlsx (usa xlsxwriter con constant_memory)
    # ------------------------------------------------------------------
    def _generate_xlsx(self):
        self.ensure_one()
        Model = self.env[self.model_name]
        domain = json.loads(self.domain or '[]')
        fields_list = json.loads(self.fields_json)
        field_names = [f['name'] for f in fields_list]
        labels = [f.get('label') or f['name'] for f in fields_list]

        buf = io.BytesIO()
        book = xlsxwriter.Workbook(
            buf, {'constant_memory': True, 'in_memory': True}
        )
        sheet = book.add_worksheet()
        header_fmt = book.add_format({'bold': True})
        for col, label in enumerate(labels):
            sheet.write(0, col, label, header_fmt)

        total = self.total_rows or 1
        row_idx = 1
        offset = 0
        rows_since_progress = 0

        while True:
            batch = Model.search_read(
                domain, field_names,
                offset=offset, limit=BATCH_SIZE, order='id',
            )
            if not batch:
                break
            for rec in batch:
                for col, fname in enumerate(field_names):
                    sheet.write(row_idx, col, self._cell_value(rec.get(fname)))
                row_idx += 1
                rows_since_progress += 1
                if rows_since_progress >= PROGRESS_EVERY:
                    pct = min(99, int((row_idx - 1) * 100 / total))
                    self._update_progress(pct)
                    rows_since_progress = 0
            offset += BATCH_SIZE

        book.close()
        return buf.getvalue()

    @staticmethod
    def _cell_value(val):
        """Normaliza valores de search_read para xlsxwriter."""
        if val is False or val is None:
            return ''
        if isinstance(val, (list, tuple)) and len(val) == 2:
            # many2one -> [id, display_name]
            return val[1]
        if isinstance(val, (list, tuple)):
            # x2many -> lista de ids; lo convertimos a texto
            return ', '.join(str(v) for v in val)
        return val

    def _update_progress(self, pct):
        """Escribe progress en el cursor PRINCIPAL y commitea.

        Evita cursor separado para no meter el thread en un race con
        snapshots REPEATABLE READ de Postgres que terminaba en
        'could not serialize access due to concurrent update' al hacer
        el write final de state='done'. El commit en el cursor principal
        también hace visible el progress al endpoint /status que corre
        en otro worker.
        """
        self.env.cr.execute(
            "UPDATE export_xlsx_job SET progress = %s WHERE id = %s",
            (pct, self.id),
        )
        self.env.cr.commit()

    # ------------------------------------------------------------------
    # Notificación al usuario vía bus.bus
    # ------------------------------------------------------------------
    def _notify_user(self):
        self.ensure_one()
        payload = {
            'type': 'se_async_export.finished',
            'job_id': self.id,
            'state': self.state,
            'name': self.name,
            'attachment_id':
                self.attachment_id.id if self.attachment_id else False,
            'error_msg': self.error_msg or '',
        }
        channel = (self.env.cr.dbname, 'res.partner',
                   self.user_id.partner_id.id)
        try:
            self.env['bus.bus'].sendone(channel, payload)
            self.env.cr.commit()
        except Exception:
            _logger.exception("No se pudo enviar bus notification job %s", self.id)

    # ------------------------------------------------------------------
    # Cron de respaldo: marca como failed los jobs running huérfanos
    # ------------------------------------------------------------------
    @api.model
    def _cron_mark_orphans(self):
        cutoff = fields.Datetime.now() - timedelta(minutes=ORPHAN_MINUTES)
        orphans = self.search([
            ('state', '=', 'running'),
            ('started_at', '<', cutoff),
        ])
        if orphans:
            orphans.write({
                'state': 'failed',
                'error_msg': _(
                    "Job aborted: sin respuesta del worker por más de %d min"
                ) % ORPHAN_MINUTES,
                'finished_at': fields.Datetime.now(),
            })
            _logger.warning("Marcados %d job(s) como huérfanos", len(orphans))
