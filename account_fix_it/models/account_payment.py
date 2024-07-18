from odoo import models, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
	_inherit = "account.payment"

	def post(self):
		t = super(AccountPayment,self).post()
		moves = self.mapped('move_line_ids.move_id')
		moves.filtered(lambda move: move.state == 'draft').post()
		return t