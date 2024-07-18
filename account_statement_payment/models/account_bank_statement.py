# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankStatement(models.Model):
	_inherit = 'account.bank.statement'

	@api.model
	def _default_journal(self):
		journal_type = self.env.context.get('journal_type', False)
		journal_check_surrender = self.env.context.get('journal_check_surrender', False)
		company_id = self.env.company.id
		if journal_type:
			journals = self.env['account.journal'].search([('type', '=', journal_type), ('company_id', '=', company_id), ('check_surrender', '=', journal_check_surrender)])
			if journals:
				return journals[0]
		return self.env['account.journal']

	journal_id = fields.Many2one(default=_default_journal)

	@api.model
	def create(self,vals):
		if self.env.context.get('journal_type') == 'cash' and self.env.context.get('journal_check_surrender'):
			id_seq = self.env['ir.sequence'].search([('name','=','Rendiciones Tesoreria')], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Rendiciones Tesoreria','implementation':'no_gap','active':True,'prefix':'REN-','padding':6,'number_increment':1,'number_next_actual' :1})
			vals['sequence_number'] = id_seq._next()
		
		elif self.env.context.get('journal_type') == 'cash':
			id_seq = self.env['ir.sequence'].search([('name','=','Caja Chica Tesoreria')], limit=1)
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Caja Chica Tesoreria','implementation':'no_gap','active':True,'prefix':'CCH-','padding':6,'number_increment':1,'number_next_actual' :1})
			vals['sequence_number'] = id_seq._next()

		t = super(AccountBankStatement,self).create(vals)
		return t

	def get_payments(self):
		self.line_ids.unlink()
		Moves = self.env['account.move'].search([('bank_statement_id', '=', self.id)])
		print(Moves.id)
		for Move in Moves:
			MoveLine = Move.line_ids.filtered(lambda line: line.account_id == self.journal_id.default_debit_account_id)
			self.env['account.bank.statement.line'].create({
													'date': Move.date,
													'ref': Move.ref,
													'name': Move.glosa,
													'partner_id': Move.partner_id.id,
													'catalog_payment_id': Move.td_payment_id.id,
													'amount': Move.amount_total if MoveLine.debit > 0 else -1 * Move.amount_total,
													'move_name': Move.name,
													'amount_currency': Move.amount_total_signed,
													'statement_id': self.id,
													'company_id': self.company_id.id,
													'journal_id': self.journal_id.id
													})
