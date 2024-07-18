# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPatrimonyTable(models.Model):
	_name = 'account.patrimony.table'

	name = fields.Char(string='Nombre')
	code = fields.Char(string='Codigo')