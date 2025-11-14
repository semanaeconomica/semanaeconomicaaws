# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import expression

class EinvoiceCatalog01(models.Model):
	_inherit = 'einvoice.catalog.01'

	def name_get(self):
		result = []
		for einv in self:
			name = einv.code + ' ' + einv.name
			result.append((einv.id, name))
		return result