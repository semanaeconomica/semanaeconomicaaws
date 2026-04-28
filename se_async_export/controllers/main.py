# -*- coding: utf-8 -*-
from odoo import _, http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class AsyncExportController(http.Controller):

    @http.route('/se_export/start', type='json', auth='user')
    def start(self, model, domain, fields, name=None):
        """Dispara un job asíncrono de export xlsx.

        Params (JSON-RPC):
          model  : str                ej. 'crm.lead'
          domain : list               ej. [['type','=','opportunity'], ...]
          fields : list[{'name','label'}]
          name   : str | None

        Return: {'job_id': int, 'total_rows': int}
        """
        if model not in request.env:
            raise UserError(_("Modelo desconocido: %s") % model)
        if not fields:
            raise UserError(_("Seleccione al menos un campo para exportar."))

        job = request.env['export.xlsx.job'].create_job(
            model_name=model,
            domain=domain or [],
            fields_list=fields,
            name=name,
        )
        return {
            'job_id': job.id,
            'total_rows': job.total_rows,
        }

    @http.route('/se_export/status', type='json', auth='user')
    def status(self, job_id):
        """Estado actual del job. Se invoca cada 3s desde el modal.

        Return: {
            'state'        : 'pending'|'running'|'done'|'failed',
            'progress'     : int 0-100,
            'total_rows'   : int,
            'attachment_url': str | False,
            'filename'     : str,
            'error_msg'    : str,
        }
        """
        job = request.env['export.xlsx.job'].browse(int(job_id))
        # La record rule garantiza que user solo ve sus propios jobs.
        # exists() devuelve recordset vacío si no existe o no tiene acceso.
        if not job.exists():
            raise AccessError(_("Job inexistente o sin permiso."))

        url = False
        filename = '%s.xlsx' % (job.name or 'export')
        if job.state == 'done' and job.attachment_id:
            url = '/web/content/%d?download=true' % job.attachment_id.id
            filename = job.attachment_id.name or filename

        return {
            'state': job.state,
            'progress': job.progress,
            'total_rows': job.total_rows,
            'attachment_url': url,
            'filename': filename,
            'error_msg': job.error_msg or '',
        }
