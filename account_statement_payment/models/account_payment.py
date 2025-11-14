# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = "account.payment"

	bank_statement_id = fields.Many2one('account.bank.statement', string='Registro de Caja')
	journal_type = fields.Selection(related='journal_id.type', string='Tipo de Diario', store=True)

	def _prepare_payment_moves(self):
		records = super(AccountPayment, self)._prepare_payment_moves()
		for record in records:
			record['bank_statement_id'] = self.bank_statement_id.id or None
			if record['journal_id'] == self.journal_id.id:
				record['ref'] = self.cash_nro_comp or ''
			if record['journal_id'] == self.destination_journal_id.id:
				record['ref'] = self.nro_comp or ''
			record['glosa'] = self.communication or ''
			for line in record['line_ids']:
				line[2]['name'] = self.communication or ''
		return records