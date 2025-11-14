# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ModelName(models.Model):
	_name = 'model.name'

	@api.model
	def _test_function(self):
		self.env.ref('account.action_account_invoice_from_list').unlink()