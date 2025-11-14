# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	def post(self):
		for move in self:
			if move.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
				for line in move.line_ids:
					line.tc = move.currency_rate if line.currency_id.name == 'USD' else 1
					line.type_document_id = move.type_document_id.id or None
					line.nro_comp = move.ref or None
		return super(AccountMove,self).post()