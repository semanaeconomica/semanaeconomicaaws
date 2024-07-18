# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalogPayment(models.Model):
	_inherit = 'einvoice.catalog.payment'

	def name_get(self):
		result = []
		for einv in self:
			name = einv.code + ' ' + einv.name
			result.append((einv.id, name))
		return result