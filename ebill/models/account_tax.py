# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError

class AccountTax(models.Model):
	_inherit = 'account.tax'

	eb_afect_igv_id = fields.Many2one('einvoice.catalog.07',string='F.E. Tipo Afectacion IGV')
	eb_tributes_type_id = fields.Many2one('einvoice.catalog.05',string='F.E. Tipo de Tributos')



