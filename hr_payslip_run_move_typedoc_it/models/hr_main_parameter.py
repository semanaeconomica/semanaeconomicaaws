# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	type_doc_pla = fields.Many2one('einvoice.catalog.01', string='Tipo de documento para asiento planilla')

