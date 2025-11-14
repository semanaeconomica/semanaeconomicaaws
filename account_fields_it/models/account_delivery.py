# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountDelivery(models.Model):
	_name = 'account.delivery'

	name = fields.Char(string='Nombre')