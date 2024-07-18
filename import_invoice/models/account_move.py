# -*- coding: utf-8 -*-

from odoo import models, fields, exceptions, api

class AccountMove(models.Model):
	_inherit = "account.move"

	code_import_invoice = fields.Many2one('delete.account.move.import',string='Codigo de Importacion Invoice',ondelete="cascade",copy=False)