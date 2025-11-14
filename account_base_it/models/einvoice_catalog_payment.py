# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalogPayment(models.Model):
	_name = 'einvoice.catalog.payment'

	@api.depends('description')
	def _get_name(self):
		for i in self:
			i.name = i.description
			
	name = fields.Char(compute=_get_name,store=True)
	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	pse_code = fields.Char(string='Codigo de Facturador', size=5)

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		recs = self.browse()
		if name:
			recs = self.search(['|',('code', '=', name),('name','=',name)] + args, limit=limit)
		if not recs:
			recs = self.search(['|',('code', operator, name),('name',operator,name)] + args, limit=limit)
		return recs.name_get()

	def name_get(self):
		result = []
		for einv in self:
			result.append([einv.id,einv.code])
		return result