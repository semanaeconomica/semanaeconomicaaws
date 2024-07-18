# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	def _prepare_invoice(self):
		invoice_vals = super(SaleOrder,self)._prepare_invoice()
		invoice_vals['doc_origin_customer'] = self.client_order_ref
		invoice_vals['invoice_origin'] = self.name + ' ' + self.client_order_ref if self.client_order_ref else self.name
		return invoice_vals