# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class LandedInvoiceBook(models.Model):
	_name = 'landed.invoice.book'
	_description = 'Landed Invoice'
	_auto = False
	
	invoice_id = fields.Many2one('account.move.line',string='Factura')
	invoice_date = fields.Date(string='Fecha Factura')
	type_document_id = fields.Many2one('einvoice.catalog.01',string='Tipo de Documento')
	nro_comp = fields.Char(string='Nro Comprobante')
	date = fields.Date(string='Fecha Contable')
	partner_id = fields.Many2one('res.partner',string='Socio')
	product_id = fields.Many2one('product.product',string='Producto')
	debit = fields.Float(string='Debe',digits=(64,2))
	amount_currency = fields.Float(string='Monto Me',digits=(64,2))
	tc = fields.Float(string='TC',digits=(12,4))
	company_id = fields.Many2one('res.company',string=u'Compañía')

	@api.model
	def init(self):
		tools.drop_view_if_exists(self._cr, 'landed_invoice_book')
		self._cr.execute("""
			CREATE VIEW landed_invoice_book AS (
				SELECT 
				row_number() OVER () AS id,
				aml.id AS invoice_id,
				am.invoice_date,
				aml.type_document_id,
				aml.nro_comp,
				am.date,
				aml.partner_id,
				aml.product_id,
				aml.debit,
				aml.amount_currency,
				aml.tc,
				am.company_id
				from account_move_line aml
				LEFT JOIN account_move am ON am.id = aml.move_id
				LEFT JOIN product_product pp ON pp.id = aml.product_id
				LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
				WHERE pt.is_landed_cost = TRUE AND aml.display_type IS NULL AND am.state = 'posted'
			)""")