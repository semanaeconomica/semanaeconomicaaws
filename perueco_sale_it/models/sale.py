# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	edition_id = fields.Many2one('product.edition.it',u'Edición')



