# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Einvoice(models.Model):
    _inherit = 'einvoice'
    total_voucher_rounded = fields.Float(compute='get_reoundeds',digits=(12,2),string="Total CPE")
    save_changes = fields.Boolean(default=False, string="Guardar Cambios",copy=False)
    related_ref = fields.Char(related='move_id.ref', string='Referencia', store=True)
    total_isc = fields.Float(string='Total ISC')
    total_discount_global = fields.Float(string='Total Descuento GLobal')
    def get_reoundeds(self):
        for record in self:
            record.total_voucher_rounded = round(record.total_voucher,2)

