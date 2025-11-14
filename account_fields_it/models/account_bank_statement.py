# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	catalog_payment_id = fields.Many2one('einvoice.catalog.payment',string='Medio de Pago')

	@api.onchange('amount_currency','currency_id','date')
	def onchange_amount_currency_it(self):
		if self.amount_currency and self.currency_id:
			self.amount = self.currency_id._convert(self.amount_currency, self.company_id.currency_id, self.company_id, self.date)
	
class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	journal_check_surrender = fields.Boolean(string='Para rendiciones', related='journal_id.check_surrender', store=True)
	sequence_number = fields.Char(string='Secuencia')

	def name_get(self):
		result = []
		for statement in self:
			if statement.journal_type == 'cash' and statement.sequence_number:
				name = statement.sequence_number
			else:
				name = statement.name
			result.append((statement.id, name))
		return result