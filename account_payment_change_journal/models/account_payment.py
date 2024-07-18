# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	@api.onchange('journal_id')
	def _onchange_journal_it(self):
		if self.journal_id:
			if self.journal_id.currency_id:
				self.currency_id = self.journal_id.currency_id
			else:
				if self.env.company.currency_id:
					self.currency_id = self.env.company.currency_id