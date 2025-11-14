# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountEfectiveType(models.Model):
	_name = 'account.efective.type'

	@api.depends('concept')
	def _get_name(self):
		for i in self:
			i.name = i.concept
			
	name = fields.Char(compute=_get_name,store=True)
	code = fields.Char(string='Codigo')
	concept = fields.Char(string='Concepto')
	group = fields.Selection([
							('E1',u'Ingresos de Operación'),
							('E2',u'Egresos de Operación'),
							('E3',u'Ingresos de Inversión'),
							('E4',u'Egresos de Inversión'),
							('E5',u'Ingresos de Financiamiento'),
							('E6',u'Engresos de Financiamiento'),
							('E7',u'Saldo Inicial'),
							('E8',u'Diferencia de Cambio')
							],string='Grupo')
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
			result.append([einv.id,einv.concept])
		return result