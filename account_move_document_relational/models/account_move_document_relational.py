# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class DocumentRelational(models.Model):
	_name = 'document.relational'
	_auto = False

	line_id = fields.Many2one('doc.invoice.relac',string='Linea Doc. Relac.')
	move_id = fields.Many2one('account.move', string='Asiento Contable')
	type_document_id = fields.Many2one('einvoice.catalog.01', string='TD')
	date = fields.Date(string='Fecha de Emision')
	nro_comprobante = fields.Char(string='Comprobante', size=40)
	amount_currency = fields.Float(string='Monto Me', digits=(16, 2))
	amount = fields.Float(string='Total Mn', digits=(16, 2))
	bas_amount = fields.Float(string='Base Imponible', digits=(16, 2))
	tax_amount = fields.Float(string='IGV', digits=(16, 2))
	journal_id = fields.Many2one('account.journal', string='Diario', required=True)
	company_id = fields.Many2one('res.company',string=u'Compañía')

	@api.model
	def init(self):
		tools.drop_view_if_exists(self._cr, 'document_relational')
		self._cr.execute("""
			CREATE VIEW document_relational AS (
				SELECT row_number() OVER () AS id, T.* FROM (
				select 
					dir.id as line_id,dir.move_id,dir.type_document_id,
					dir.date,dir.nro_comprobante,dir.amount_currency,
        			dir.amount,dir.bas_amount,dir.tax_amount,am.journal_id,am.company_id
 				from doc_invoice_relac dir
 				LEFT JOIN account_move am ON am.id = dir.move_id
				)T
			)""")