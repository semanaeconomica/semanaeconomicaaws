# -*- coding: utf-8 -*-
import base64
import io
import logging
import xlsxwriter
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


class CrmExportWizard(models.TransientModel):
    _name = 'crm.export.wizard'
    _description = 'Wizard para exportar oportunidades'

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Listo'),
    ], default='draft')
    file_data = fields.Binary('Archivo', readonly=True)
    file_name = fields.Char('Nombre del archivo', default='oportunidades.xlsx')
    record_count = fields.Integer('Registros exportados', readonly=True)
    total_to_export = fields.Integer('Total a exportar', readonly=True)
    export_mode = fields.Selection([
        ('selected', 'Solo seleccionados'),
        ('filtered', 'Todos los filtrados'),
    ], default='selected', string='Modo de exportacion')

    @api.model
    def default_get(self, fields_list):
        res = super(CrmExportWizard, self).default_get(fields_list)
        context = self.env.context
        active_ids = context.get('active_ids', [])
        active_domain = context.get('active_domain', [])

        Lead = self.env['crm.lead']
        if active_domain:
            total_filtered = Lead.search_count(active_domain)
            res['total_to_export'] = total_filtered
            res['export_mode'] = 'filtered'
        else:
            res['total_to_export'] = len(active_ids)
            res['export_mode'] = 'selected'

        return res

    def action_export(self):
        self.ensure_one()
        Lead = self.env['crm.lead']
        context = self.env.context
        active_ids = context.get('active_ids', [])
        active_domain = context.get('active_domain', [])

        if self.export_mode == 'filtered' and active_domain:
            domain = active_domain
        elif active_ids:
            domain = [('id', 'in', active_ids)]
        else:
            domain = []

        total = Lead.search_count(domain)
        _logger.info('CRM Export: iniciando exportacion de %s registros, domain=%s', total, domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'constant_memory': True})
        worksheet = workbook.add_worksheet('Oportunidades')

        header_fmt = workbook.add_format({
            'bold': True,
            'bg_color': '#875A7B',
            'font_color': 'white',
            'border': 1,
        })
        date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        headers = [
            'ID', 'Oportunidad', 'Contacto', 'Email',
            'Telefono', 'Movil', 'Empresa', 'Vendedor',
            'Equipo de ventas', 'Etapa', 'Ingreso esperado',
            'Probabilidad', 'Fecha de creacion', 'Fecha de cierre',
            'Prioridad', 'Tipo', 'Estado',
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_fmt)

        row = 1
        offset = 0

        while offset < total:
            leads = Lead.search(domain, limit=BATCH_SIZE, offset=offset, order='id')
            for lead in leads:
                worksheet.write(row, 0, lead.id)
                worksheet.write(row, 1, lead.name or '')
                worksheet.write(row, 2, lead.partner_id.name or '')
                worksheet.write(row, 3, lead.email_from or '')
                worksheet.write(row, 4, lead.phone or '')
                worksheet.write(row, 5, lead.mobile or '')
                worksheet.write(row, 6, lead.partner_name or '')
                worksheet.write(row, 7, lead.user_id.name or '')
                worksheet.write(row, 8, lead.team_id.name or '')
                worksheet.write(row, 9, lead.stage_id.name or '')
                worksheet.write(row, 10, lead.expected_revenue or 0)
                worksheet.write(row, 11, lead.probability or 0)
                if lead.create_date:
                    worksheet.write_datetime(row, 12, lead.create_date.replace(tzinfo=None), date_fmt)
                if lead.date_closed:
                    worksheet.write_datetime(row, 13, lead.date_closed.replace(tzinfo=None), date_fmt)
                worksheet.write(row, 14, lead.priority or '')
                worksheet.write(row, 15, lead.type or '')
                worksheet.write(row, 16, 'Ganado' if lead.won_status == 'won' else ('Perdido' if lead.won_status == 'lost' else 'En proceso'))
                row += 1

            offset += BATCH_SIZE
            leads.invalidate_cache()
            _logger.info('CRM Export: procesados %s/%s registros', min(offset, total), total)

        workbook.close()
        output.seek(0)

        self.write({
            'state': 'done',
            'file_data': base64.b64encode(output.read()),
            'file_name': 'oportunidades_%s.xlsx' % fields.Date.today(),
            'record_count': row - 1,
        })
        output.close()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }
