# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
	_inherit = 'sale.order'

	can_edit_field = fields.Boolean(string='Puede ver', compute='_compute_can_edit_field_sale')

	@api.onchange('partner_id')
	def _compute_can_edit_field_sale(self):
		for record in self:
			user = self.env.user
			record.can_edit_field = user.has_group('vinculate_sale_invoice_group.group_edit_invoice')


# class SaleOrderLine(models.Model):
# 	_inherit = "sale.order.line"

# 	can_edit_field = fields.Boolean(string='Puede ver', compute='_compute_can_edit_field_sale_order_line')
# 	# purchase_price = fields.Float(
# 	# 	string='Cost', compute="_compute_purchase_price",
# 	# 	digits='Product Price', store=True, readonly=False)
# 	@api.onchange('product_id')
# 	def _compute_can_edit_field_sale_order_line(self):
# 		for record in self:
# 			user = self.env.user
# 			record.can_edit_field = user.has_group('vinculate_sale_invoice_group.group_edit_invoice')
