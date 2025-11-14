# -*- coding: utf-8 -*-

from odoo import api, fields, models

class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def _prepare_invoice_values(self, order, name, amount, so_line):
		invoice_dicc = super(SaleAdvancePaymentInv,self)._prepare_invoice_values(order, name, amount, so_line)
		invoice_dicc['doc_origin_customer'] = order.client_order_ref
		invoice_dicc['invoice_origin'] = order.name + ' ' + order.client_order_ref if order.client_order_ref else order.name

		return invoice_dicc