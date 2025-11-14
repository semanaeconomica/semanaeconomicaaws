# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
	_inherit = 'account.move'

	def _check_journal_period_close(self):
		for move in self:
			print('check')
			period = self.env['account.journal.period'].search([('company_id','=',move.company_id.id),('date_start','<=',move.date),('date_end','>=',move.date)],limit=1)
			if period:
				if period.state == 'done':
					raise UserError('No puede agregar / modificar entradas anteriores e inclusive a la fecha de bloqueo %s - %s.'%(period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d')))
				else:
					for line in period.line_ids:
						if line.journal_id == move.journal_id and line.state == 'done':
							raise UserError('No puede agregar / modificar entradas del diario "%s" anteriores e inclusive a la fecha de bloqueo %s - %s.'%(line.journal_id.name,period.date_start.strftime('%Y/%m/%d'),period.date_end.strftime('%Y/%m/%d')))

		return True

	def write(self, vals):
		res = True
		for move in self:
			print('write move')
			move._check_journal_period_close()
			res |= super(AccountMove, move).write(vals)
		return res
			
	@api.model_create_multi
	def create(self, vals_list):
		rslt = super(AccountMove, self).create(vals_list)
		print('create move')
		self._check_journal_period_close()
		return rslt

	def unlink(self):
		print('unlink move')
		self._check_journal_period_close()
		res = super(AccountMove, self).unlink()
		return res

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.model_create_multi
	def create(self, vals_list):
		print('create move line')
		res = super(AccountMoveLine, self).create(vals_list)
		moves = res.mapped('move_id')
		moves._check_journal_period_close()
		return res

	def write(self, vals):
		result = True
		for line in self:
			print('write move line')
			print(vals)
			if 'full_reconcile_id' in vals or 'reconciled' in vals or 'amount_residual' in vals or 'amount_residual_currency' in vals:
				result |= super(AccountMoveLine, line).write(vals)
			else:
				line.move_id._check_journal_period_close()
				result |= super(AccountMoveLine, line).write(vals)

		return result

	def unlink(self):
		moves = self.mapped('move_id')
		print('unlink move line')
		moves._check_journal_period_close()
		res = super(AccountMoveLine, self).unlink()
		return res