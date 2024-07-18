# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountReconciliation(models.AbstractModel):
	_inherit = 'account.reconciliation.widget'

	@api.model
	def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, recs_count=0):
		ret = super(AccountReconciliation,self)._prepare_move_lines(move_lines,target_currency,target_date,recs_count)
		for line in ret:
			move_line = next(filter(lambda l:l.id == line['id'],move_lines),None)
			line['nro_comp'] = move_line.nro_comp if move_line else None
			line['type_document_id'] = move_line and move_line.type_document_id.id if move_line.type_document_id else None
		return ret