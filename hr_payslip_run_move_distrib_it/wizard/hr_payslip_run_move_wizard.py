# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrPayslipRunMoveWizard(models.TransientModel):
	_inherit = 'hr.payslip.run.move.wizard'


	def generate_move(self):
		extra_line = {}
		if self.debit > self.credit:
			extra_line = {
						'account_id': self.account_id.id,
						'debit': 0,
						'credit': self.difference,
						'name': 'Ajuste'}
		if self.credit > self.debit:
			extra_line = {
						'account_id': self.account_id.id,
						'debit': self.difference,
						'credit': 0,
						'name': 'Ajuste'}
		
		lines = self.env['hr.payslip.run.move.dist'].search([])
		PR = self.env['hr.payslip.run'].browse(self._context.get('payslip_run_id'))
		extra_line = [(0, 0, extra_line)] if extra_line else []
		move = self.env['account.move'].create({
				'journal_id': self.journal_id.id,
				'date': PR.date_end,
				'ref': 'Planilla - %s' % PR.name,
				'line_ids': extra_line + [
											(0, 0, {
												'account_id': line.account_id.id,
												'debit': line.debit,
												'credit': line.credit,
												'name': line.salary_rule_id.name or '',
												'analytic_account_id': line['analytic_account_id'].id if line['analytic_account_id'].id else None,
												'partner_id':line['partner_id'].id if line['partner_id'].id else None,
											}) for line in lines
										]
			})
		move.action_post()
		PR.account_move_id = move.id
		PR.state = 'close'
		return self.env['popup.it'].get_message('Generacion de Asiento Exitosa')


