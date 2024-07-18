# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ItInvoiceSerie(models.Model):
	_name = 'it.invoice.serie'

	name = fields.Char(string='Nombre')
	document_type_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	sequence_id = fields.Many2one('ir.sequence',string='Secuencia')
	description = fields.Char(string=u'Descripción')
	manual = fields.Boolean(string='Es manual', default=False)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)