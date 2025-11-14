# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountCashFlow(models.Model):
	_name = 'account.cash.flow'

	@api.depends('item')
	def _get_name(self):
		for i in self:
			i.name = i.item
			
	name = fields.Char(compute=_get_name,store=True)
	code = fields.Char(string='Codigo',size=6)
	item = fields.Char(string='Rubro')
	group = fields.Char(string='Grupo')
	order = fields.Integer(string='Orden')

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
