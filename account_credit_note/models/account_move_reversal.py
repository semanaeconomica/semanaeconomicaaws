# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _

class AccountMoveReversal(models.TransientModel):
	_inherit = 'account.move.reversal'

	def reverse_moves(self):
		moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
		credit_note = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dt_national_credit_note

		# Create default values.
		default_values_list = []
		for move in moves:
			default_values_list.append({
				'ref': self.reason if self.reason else '',
				'date': self.date or move.date,
				'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
				'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
				'type_document_id': credit_note.id or '',
				'invoice_payment_term_id': None,
				'auto_post': True if self.date > fields.Date.context_today(self) else False,
				'doc_invoice_relac': [(0, 0, {'type_document_id': move.type_document_id.id,
											  'date': move.invoice_date,
											  'nro_comprobante': move.ref,
											  'amount_currency': move.amount_total if move.currency_id.name != 'PEN' else 0,
											  'amount': abs(move.amount_total_signed)}
											)]
			})

		# Handle reverse method.
		if self.refund_method == 'cancel':
			if any([vals.get('auto_post', False) for vals in default_values_list]):
				new_moves = moves._reverse_moves(default_values_list)
			else:
				new_moves = moves._reverse_moves(default_values_list, cancel=True)
		elif self.refund_method == 'modify':
			moves._reverse_moves(default_values_list, cancel=True)
			moves_vals_list = []
			for move in moves.with_context(include_business_fields=True):
				moves_vals_list.append(move.copy_data({
					'invoice_payment_ref': move.name,
					'date': self.date or move.date,
				})[0])
			new_moves = self.env['account.move'].create(moves_vals_list)
		elif self.refund_method == 'refund':
			new_moves = moves._reverse_moves(default_values_list)
		else:
			return

		# Create action.
		action = {
			'name': _('Reverse Moves'),
			'type': 'ir.actions.act_window',
			'res_model': 'account.move',
		}
		if len(new_moves) == 1:
			new_moves._get_ref()
			action.update({
				'view_mode': 'form',
				'res_id': new_moves.id,
			})
		else:
			for i in new_moves:
				i._get_ref()
			action.update({
				'view_mode': 'tree,form',
				'domain': [('id', 'in', new_moves.ids)],
			})
		return action