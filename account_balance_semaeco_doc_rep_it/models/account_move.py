from odoo import api, fields, models
from odoo.exceptions import UserError


class account_move(models.Model):
	_inherit = "account.move"
	
	date_aprox_payment = fields.Date(u'Fecha Canc. Aprox.')
	manage_comment = fields.Text(u'Comentario de Gestión')
	responsible_followup_id = fields.Many2one('responsible.followup',related='partner_id.responsible_followup_id',string='Responsable de Seguimiento', store=True)


	@api.constrains('date_aprox_payment')
	def change_date_aprox_payment(self):
		for move in self:
			lines = move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
			lines.expected_pay_date = move.date_aprox_payment


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	def update_expected_date_it(self):
		expected_date = self.env.context['expected_date']
		for line in self:
			line.expected_pay_date = expected_date
			if line.move_id.type != 'entry':
				line.env.cr.execute("UPDATE ACCOUNT_MOVE SET date_aprox_payment = '%s' WHERE ID = %d"%(expected_date.strftime('%Y/%m/%d'),line.move_id.id))