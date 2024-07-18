# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog01(models.Model):
	_name = 'einvoice.catalog.01'

	@api.depends('description')
	def _get_name(self):
		for i in self:
			i.name = i.description

	name = fields.Char(compute=_get_name,store=True)
	code = fields.Char(string='Codigo')
	description = fields.Char(string='Descripcion')
	digits_serie = fields.Integer(string='Digitos Serie')
	digits_number = fields.Integer(string='Digitos Numero')

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		einvoice_ids = []
		if name:
			einvoice_ids = self._search(['|',('name', '=', name),('code','=',name)] + args, limit=limit, access_rights_uid=name_get_uid)
		if not einvoice_ids:
			einvoice_ids = self._search(['|',('name', operator, name),('code', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(einvoice_ids).name_get()

	def name_get(self):
		result = []
		for einv in self:
			result.append([einv.id,einv.code])
		return result