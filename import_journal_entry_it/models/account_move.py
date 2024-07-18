# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	code_import = fields.Many2one('delete.journal.entry.import',string='Codigo de Importacion',ondelete="cascade",copy=False)