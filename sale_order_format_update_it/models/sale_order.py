# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order(models.Model):
	_inherit = 'sale.order'

	def action_update_format(self):
		for l in self:
			for j in l.order_line:
				j.format_id = j.product_id.product_tmpl_id.format_id.id




class SaleUpdateFormat(models.TransientModel):
	_name = 'sale.update.format'

	def update_format(self):
		for record in self.env['sale.order'].search([]):
			for j in record.order_line:
				j.format_id = j.product_id.product_tmpl_id.format_id.id			