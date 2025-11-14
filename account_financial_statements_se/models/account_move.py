# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	#canje_se = fields.Selection([('canje','CANJE'),('cash','EFECTIVO')],string='Canje')
	patrimony_table_id = fields.Many2one('account.patrimony.table',string='Concepto Patrimonio')