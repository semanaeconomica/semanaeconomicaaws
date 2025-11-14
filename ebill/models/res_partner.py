# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	state_id = fields.Many2one('res.country.state', string='Departamento')
	province_id = fields.Many2one('res.country.state', string='Provincia')
	district_id = fields.Many2one('res.country.state', string='Distrito')

	def _display_address(self, without_company=False):

		'''
		The purpose of this function is to build and return an address formatted accordingly to the
		standards of the country where it belongs.

		:param address: browse record of the res.partner to format
		:returns: the address formatted in a display that fit its country habits (or the default ones
			if not country is specified)
		:rtype: string
		'''
		# get the information that will be injected into the display format
		# get the address format
		address_format = self.country_id.address_format or \
			  "%(street)s\n%(street2)s\n%(state_name)s-%(province_name)s-%(district_code)s %(zip)s\n%(country_name)s"
		args = {
			'district_code': self.district_id.code or '',
			'district_name': self.district_id.name or '',
			'province_code': self.province_id.code or '',
			'province_name': self.province_id.name or '',
			'state_code': self.state_id.code or '',
			'state_name': self.state_id.name or '',
			'country_code': self.country_id.code or '',
			'country_name': self.country_id.name or '',
			'company_name': self.parent_name or '',
		}
		for field in self._address_fields():
			args[field] = getattr(self, field) or ''
		if without_company:
			args['company_name'] = ''
		elif self.commercial_company_name:
			address_format = '%(company_name)s\n' + address_format
		return address_format % args