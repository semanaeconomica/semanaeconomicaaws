# -*- coding: utf-8 -*-

from odoo import models, fields, api

class DummyModel(models.TransientModel):
	_name = 'dummy.model'
	_description = "holas"

	@api.model
	def update_records(self):
		for catalog in self.env['einvoice.catalog.01'].search([]):
			if catalog.code == '01':
				catalog.pse_code = '1'
			if catalog.code == '03':
				catalog.pse_code = '2'
			if catalog.code == '07':
				catalog.pse_code = '3'
			if catalog.code == '08':
				catalog.pse_code = '4'
		for currency in self.env['res.currency'].search([]):
			if currency.name == 'PEN':
				currency.pse_code = '1'
			if currency.name == 'USD':
				currency.pse_code = '2'
			if currency.name == 'EUR':
				currency.pse_code = '3'

	@api.model
	def delete_states(self):
		country = self.env['res.country'].search([('code','=','PE')],limit=1)
		self.env['res.country.state'].search([('country_id','=',country.id)]).unlink()