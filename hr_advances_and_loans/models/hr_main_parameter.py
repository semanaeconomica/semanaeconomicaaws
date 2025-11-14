# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	grat_advance_input_id = fields.Many2one('hr.payslip.input.type', string='Input Adelanto de Gratificacion')