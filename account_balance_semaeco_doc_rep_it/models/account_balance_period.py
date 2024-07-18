# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang

class AccountBalancePeriodBook(models.Model):
	_inherit = 'account.balance.period.book'

	manage_comment = fields.Text(u'Comentario de Gestión')

	def update_expected_date_it(self):
		expected_date = self.env.context['expected_date']
		for line in self:
			line.move_line_id.expected_pay_date = expected_date
			if line.move_id.type != 'entry':
				line.env.cr.execute("UPDATE ACCOUNT_MOVE SET date_aprox_payment = '%s' WHERE ID = %d"%(expected_date.strftime('%Y/%m/%d'),line.move_id.id))