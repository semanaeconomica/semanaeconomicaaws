# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRunMove(models.Model):
	_name = 'hr.payslip.run.move'
	_auto = False
	_order = 'sequence'

	salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial')
	sequence = fields.Integer(string='Secuencia')
	code = fields.Char(related='salary_rule_id.code', string='Codigo')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	account_id = fields.Many2one('account.account', string='Cuenta Contable')
	debit = fields.Float(string='Debe')
	credit = fields.Float(string='Haber')