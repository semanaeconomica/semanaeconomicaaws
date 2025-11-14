from odoo import models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
	_inherit = "account.move"

	def action_concile_special(self):
		for move in self:
				self._cr.execute("""update account_move_line set amount_residual = 0, amount_residual_currency = 0, reconciled=TRUE where move_id = %d"""%(move.id))
		return self.env['popup.it'].get_message(u'Se aplicó la conciliación especial.')

	def action_reconcile_special(self):
		for move in self:
				self._cr.execute("""update account_move_line set reconciled=FALSE where move_id = %d"""%(move.id))
		return self.env['popup.it'].get_message(u'Se quitó la conciliación especial.')