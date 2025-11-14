from odoo import models, fields, api

try:
    class EinvoiceCatalog08(models.Model):
        _name = 'einvoice.catalog.08'
        _description = "holas"
        name = fields.Char(string='Nombre')
        code = fields.Char(string='Codigo', size=3)
        code_fact = fields.Char(string='Codigo facturador', size=3)
except:
    class EinvoiceCatalog08(models.Model):
        _inherit = 'einvoice.catalog.08'




