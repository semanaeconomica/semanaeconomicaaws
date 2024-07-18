# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslipRunMoveDist(models.Model):
	_name = 'hr.payslip.run.move.dist'
	_auto = False
	_order = 'sequence'

	salary_rule_id = fields.Many2one('hr.salary.rule', string='Regla Salarial')
	sequence = fields.Integer(string='Secuencia')
	code = fields.Char(related='salary_rule_id.code', string='Codigo')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analitica')
	account_id = fields.Many2one('account.account', string='Cuenta Contable')
	debit = fields.Float(string='Debe')
	credit = fields.Float(string='Haber')
	partner_id = fields.Many2one('res.partner','Socio')


class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'


	def get_sql(self):
		sql = """
				CREATE OR REPLACE VIEW hr_payslip_run_move_dist AS
				(
					SELECT row_number() OVER () AS id, *
					FROM payslip_run_analytic_move_distrib(%d, %d)
					where debit!=0 or credit!=0
				)
			""" % (self.id, self.env.company.id)
		return sql

	def get_move_wizard(self):
		print('holaaaa')
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		if self.account_move_id:
			raise UserError('Elimine el Asiento Actual para generar uno nuevo')
		self._cr.execute(self.get_sql())
		lines = self.env['hr.payslip.run.move.dist'].search([])
		total_credit = total_debit = 0
		for line in lines:
			total_credit += line.credit
			total_debit += line.debit
		return {
			'name': 'Generar Asiento Contable',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.payslip.run.move.wizard',
			'views': [(self.env.ref('hr_payslip_run_move_it.payslip_run_generation_move_wizard_form').id, 'form')],
			'context': {'default_credit': total_credit,
						'default_debit': total_debit,
						'payslip_run_id': self.id},
			'target': 'new'
		}	
