# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
	_inherit = 'account.move'

	bank_statement_id = fields.Many2one('account.bank.statement', string='Registro de Caja')