# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_landed_cost = fields.Boolean(string='Se usa en Gasto Vinculado',default=False)

