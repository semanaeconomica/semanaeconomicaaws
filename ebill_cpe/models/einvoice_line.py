# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceLine(models.Model):
    _inherit = 'einvoice.line'
    save_changes = fields.Boolean(default=False, string="Guardar Cambios",copy=False)
    move_line_id = fields.Many2one('account.move.line',ondelete='cascade')
    code = fields.Char(string='Codigo')
    uom = fields.Char(string='Unidad de Medida')
    unit_value = fields.Float(string='Valor Unitario',digits=(12,10))
    unit_price = fields.Float(string='Precio Unitario',digits=(12,10))
    discount_value = fields.Float(string='Valor Descuento',digits=(12,10))
    percentage_discount = fields.Float(string='Porcentaje Descuento',digits=(12,10))
    sunat_product_code = fields.Char(string='Codigo Producto SUNAT')
    igv_type = fields.Char(string='Tipo de IGV',size=2)

    subtotal = fields.Float(string='Subtotal Redondeado',digits=(12,10))
    subtotal_origin = fields.Float(string='Subtotal Real',digits=(12,10))

    igv = fields.Float(string='IGV Redondeado',digits=(12,10))
    igv_origin = fields.Float(string='IGV Real',digits=(12,10))

    icbper = fields.Float(string='ICBPER',digits=(12,10))

    total = fields.Float(string='Total',digits=(12,10))
    total_origin = fields.Float(string='Total', digits=(12, 10))

    advance_regularization = fields.Boolean(string='Anticipo Regularizacion',default=False)
    advance_document_serie = fields.Char(string='Anticipo Serie Documento')
    advance_document_number = fields.Char(string='Anticipo Numero Documento')

    isc_type = fields.Char(string='Tipo de ISC', size=2)
    isc = fields.Float(string='Total ISC', digits=(12, 2))