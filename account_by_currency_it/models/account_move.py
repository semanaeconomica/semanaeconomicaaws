# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _
from odoo.exceptions import ValidationError, RedirectWarning


class AccountMove(models.Model):
	_inherit = "account.move"

	def _recompute_payment_terms_lines(self):
		''' Compute the dynamic payment term lines of the journal entry.'''
		self.ensure_one()
		in_draft_mode = self != self._origin
		today = fields.Date.context_today(self)

		def _get_payment_terms_computation_date(self):
			''' Get the date from invoice that will be used to compute the payment terms.
			:param self:    The current account.move record.
			:return:        A datetime.date object.
			'''
			if self.invoice_payment_term_id:
				return self.invoice_date or today
			else:
				return self.invoice_date_due or self.invoice_date or today

		def _get_payment_terms_account(self, payment_terms_lines):
			''' Get the account from invoice that will be set as receivable / payable account.
			:param self:                    The current account.move record.
			:param payment_terms_lines:     The current payment terms lines.
			:return:                        An account.account record.
			'''
			if payment_terms_lines:
				# Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
				return payment_terms_lines[0].account_id
			elif self.partner_id:
				# Retrieve account from main.parameter.
				param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
				if param:
					account_it = self.env['currency.parameter.line'].search([('main_parameter_id','=',param.id),('currency_id','=',self.currency_id.id)],limit=1)
					if account_it:
						if self.is_sale_document(include_receipts=True):
							return account_it.credit_account_id
						else:
							return account_it.debit_account_id

				if self.is_sale_document(include_receipts=True):
					return self.partner_id.property_account_receivable_id
				else:
					return self.partner_id.property_account_payable_id
			else:
				# Search new account.
				domain = [
					('company_id', '=', self.company_id.id),
					('internal_type', '=', 'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
				]
				return self.env['account.account'].search(domain, limit=1)

		def _compute_payment_terms(self, date, total_balance, total_amount_currency):
			''' Compute the payment terms.
			:param self:                    The current account.move record.
			:param date:                    The date computed by '_get_payment_terms_computation_date'.
			:param total_balance:           The invoice's total in company's currency.
			:param total_amount_currency:   The invoice's total in invoice's currency.
			:return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
			'''
			if self.invoice_payment_term_id:
				to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.currency_id)
				if self.currency_id != self.company_id.currency_id:
					# Multi-currencies.
					to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
					return [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
				else:
					# Single-currency.
					return [(b[0], b[1], 0.0) for b in to_compute]
			else:
				return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

		def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):
			''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
			:param self:                    The current account.move record.
			:param existing_terms_lines:    The current payment terms lines.
			:param account:                 The account.account record returned by '_get_payment_terms_account'.
			:param to_compute:              The list returned by '_compute_payment_terms'.
			'''
			# As we try to update existing lines, sort them by due date.
			existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
			existing_terms_lines_index = 0

			# Recompute amls: update existing line or create new one for each payment term.
			new_terms_lines = self.env['account.move.line']
			for date_maturity, balance, amount_currency in to_compute:
				if self.journal_id.company_id.currency_id.is_zero(balance) and len(to_compute) > 1:
					continue

				if existing_terms_lines_index < len(existing_terms_lines):
					# Update existing line.
					candidate = existing_terms_lines[existing_terms_lines_index]
					existing_terms_lines_index += 1
					candidate.update({
						'date_maturity': date_maturity,
						'amount_currency': -amount_currency,
						'debit': balance < 0.0 and -balance or 0.0,
						'credit': balance > 0.0 and balance or 0.0,
					})
				else:
					# Create new line.
					create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
					candidate = create_method({
						'name': self.invoice_payment_ref or '',
						'debit': balance < 0.0 and -balance or 0.0,
						'credit': balance > 0.0 and balance or 0.0,
						'quantity': 1.0,
						'amount_currency': -amount_currency,
						'date_maturity': date_maturity,
						'move_id': self.id,
						'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
						'account_id': account.id,
						'partner_id': self.commercial_partner_id.id,
						'exclude_from_invoice_tab': True,
					})
				new_terms_lines += candidate
				if in_draft_mode:
					candidate._onchange_amount_currency()
					candidate._onchange_balance()
			return new_terms_lines

		existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
		others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
		total_balance = sum(others_lines.mapped('balance'))
		total_amount_currency = sum(others_lines.mapped('amount_currency'))

		if not others_lines:
			self.line_ids -= existing_terms_lines
			return

		computation_date = _get_payment_terms_computation_date(self)
		account = _get_payment_terms_account(self, existing_terms_lines)
		to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
		new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

		# Remove old terms lines that are no longer needed.
		self.line_ids -= existing_terms_lines - new_terms_lines

		if new_terms_lines:
			self.invoice_payment_ref = new_terms_lines[-1].name or ''
			self.invoice_date_due = new_terms_lines[-1].date_maturity

	@api.onchange('currency_id')
	def _onchange_currency_it_account(self):
		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		account_it = None
		if param:
			account_it = self.env['currency.parameter.line'].search([('main_parameter_id','=',param.id),('currency_id','=',self.currency_id.id)],limit=1)

		if self.is_sale_document(include_receipts=True):
			if account_it:
				new_term_account = account_it.credit_account_id
			else:
				new_term_account = self.partner_id.commercial_partner_id.property_account_receivable_id
		elif self.is_purchase_document(include_receipts=True):
			if account_it:
				new_term_account = account_it.debit_account_id
			else:
				new_term_account = self.partner_id.commercial_partner_id.property_account_payable_id
		else:
			new_term_account = None

		filtered_line = self.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable','payable'])
		filtered_line.account_id = new_term_account