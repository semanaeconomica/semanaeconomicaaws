# -*- coding:utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'res.users'
    signature_up = fields.Binary(string="Sube tu Firma")

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    digital_signature = fields.Binary(string="Firma Vendedor",compute="get_digital_signature")
    #signature_up = fields.Binary(string="Firma Vendedor", related="user_id.signature_up")
    @api.onchange('digital_signature')
    def get_digital_signature(self):
        for record in self:
            if record.user_id.signature_up:
                record.digital_signature = record.user_id.signature_up
            else:
                record.digital_signature = record.user_id.digital_signature



