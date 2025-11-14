# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPettyCash(models.Model):
	_name = 'account.petty.cash'

	name = fields.Char(string='Nombre')