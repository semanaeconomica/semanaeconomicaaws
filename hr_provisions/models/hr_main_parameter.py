# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	provision_journal_id = fields.Many2one('account.journal', string='Diario')

