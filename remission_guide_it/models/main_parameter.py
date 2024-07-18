# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
BILLING_TYPE = [('0','Nubefact')]

class MainParameter(models.Model):
	_inherit = 'main.parameter'
	
	web_guides_query = fields.Char(string=u'Web consulta')
	billing_type = fields.Selection(BILLING_TYPE,string='Tipo de Facturador')
	guide_series_ids = fields.One2many('remission.guide.series','parameter_id')

class RemissionGuideSeries(models.Model):
	_name = 'remission.guide.series'

	parameter_id = fields.Many2one('main.parameter', string='Parameter')
	series_id = fields.Many2one('ir.sequence',string='Serie',required=True)
	token = fields.Char(u'Token NubeFact',required=True)
	path = fields.Char(u'URL NubeFact',required=True)
	billing_type = fields.Selection(BILLING_TYPE,string='Tipo de Facturador')

	@api.constrains('series_id')
	def _verify_series_id(self):
		for elem in self:
			exist = elem.search([('series_id','=',elem.series_id.id)])
			if len(exist)>1:
				raise UserError(u'Ya existe un parámetro con la serie: '+elem.series_id.name)