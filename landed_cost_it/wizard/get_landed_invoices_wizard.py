# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetLandedInvoices(models.TransientModel):
	_name = "get.landed.invoices.wizard"
	
	landed_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	invoices = fields.Many2many('landed.invoice.book','get_invoice_landed_book_rel','invoice_id','get_landed_invoice_id',string=u'Invoices', required=True)
		
	def insert(self):
		vals=[]
		for invoice in self.invoices:
			val = {
				'landed_id': self.landed_id.id,
				'invoice_id': invoice.invoice_id.id,
				'invoice_date': invoice.invoice_date,
				'type_document_id': invoice.type_document_id.id,
				'nro_comp': invoice.nro_comp,
				'date': invoice.date,
				'partner_id': invoice.partner_id.id,
				'product_id': invoice.product_id.id,
				'debit': invoice.debit,
				'amount_currency': invoice.amount_currency,
				'tc': invoice.tc,
				'company_id': invoice.company_id.id,
			}
			vals.append(val)
		self.env['landed.cost.invoice.line'].create(vals)
		self.landed_id._change_flete()