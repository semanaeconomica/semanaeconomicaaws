# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
	_inherit = 'main.parameter'
	discounts_products_ids = fields.Many2many('product.product',string="Productos Descuentos")

