# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def _prepare_payment_moves(self):
		records = super(AccountPayment,self)._prepare_payment_moves()
		for record in records:
			record['td_payment_id'] = self.catalog_payment_id.id or None
			if record['journal_id'] == self.journal_id.id:
				for line in record['line_ids']:
					if line[2]['account_id'] == self.journal_id.default_debit_account_id.id or line[2]['account_id'] == self.journal_id.default_credit_account_id.id:
						line[2]['cash_flow_id'] = self.cash_flow_id.id or None
						line[2]['type_document_id'] = self.type_doc_cash_id.id or None
						line[2]['nro_comp'] = self.cash_nro_comp or None
					else:
						line[2]['type_document_id'] = self.type_document_id.id or None
						line[2]['nro_comp'] = self.nro_comp or None
					line[2]['tc'] = self.aux_type_change if self.currency_id.name == 'USD' else 1 
			if record['journal_id'] == self.destination_journal_id.id:
				for line in record['line_ids']:
					line[2]['type_document_id'] = self.type_document_id.id or None
					line[2]['nro_comp'] = self.nro_comp or None
					line[2]['tc'] = self.aux_type_change if self.currency_id.name == 'USD' else 1

		return records