from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAsset(models.Model):
	_inherit = 'account.asset'

	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento', copy=False)
	nro_comp = fields.Char(string='Nro Comprobante', copy=False)