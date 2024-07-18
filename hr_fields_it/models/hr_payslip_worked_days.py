# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipWorkedDays(models.Model):
	_inherit = 'hr.payslip.worked_days'

	wd_type_id = fields.Many2one('hr.payslip.worked_days.type', string='Worked Day Type')
	name = fields.Char(related='wd_type_id.name')
	code = fields.Char(related='wd_type_id.code')
	rate = fields.Integer(related='wd_type_id.rate', string='Tasa o Monto')
	work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Type', required=False, help="The code that can be used in the salary rules")