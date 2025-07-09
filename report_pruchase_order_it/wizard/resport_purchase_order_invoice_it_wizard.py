# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ReportMrpBomLineWizard(models.TransientModel):
	_name = 'resport.purchase.order.invoice.it.wizard'
	_description = "Wizard para poder crear la vista reporte de rendimiento de ordenes de compra"


	product_id = fields.Many2one('product.product', string=u'Producto')
	date_start = fields.Date(string=u'Fecha inicio',required=True)
	date_end = fields.Date(string=u'Fecha fin',required=True)

	def get_view_orders(self):
		if not self.date_start or not self.date_end:
			raise UserError("Es necesario que llene ambos campos \n-Fecha de inicio\n-Fecha de fin")
		return self.env['resport.purchase.order.invoice.it'].sudo().get_view_orders_report(self.date_start, self.date_end)
