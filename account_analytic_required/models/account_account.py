# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models
from odoo.tools import float_is_zero


class AccountAccount(models.Model):
	_inherit = "account.account"

	analytic_policy = fields.Selection(
		selection=[('optional', 'Opcional'),
				   ('always', 'Siempre'),
				   ('never', 'Nunca')],
		string=u'Política para las cuentas analíticas',
		required=True,
		default='optional')