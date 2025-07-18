# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_compare
import pytz
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import urllib.parse
import requests
import json

class ResCurrencyRate(models.Model):
	_inherit = 'res.currency.rate'
	date_update_rate = fields.Datetime(string="Fecha Actualizacion")

class ResCurrency(models.Model):
	_inherit = "res.currency"

	def _update_rates(self,date,buy,sale,currency):
		#currency = self.env.ref('base.USD')
		currency_rate = self.env['res.currency.rate']
		for cmpny in self.env['res.company'].search([]):
			rate = currency_rate.search([
				('currency_id', '=', currency.id),
				('name', '=', date),
				('company_id', '=', cmpny.id),
			], limit=1)
			if not rate:
				currency_rate.create({
					'currency_id': currency.id,
					'rate': 1.0 / sale,
					'name': date,
					'sale_type': sale,
					'purchase_type': buy,
					'company_id': cmpny.id,
					'date_update_rate': fields.Datetime.now()
				})
			else:
				rate.write({
					'rate': 1.0 / sale,
					'sale_type': sale,
					'purchase_type': buy,
					'date_update_rate': fields.Datetime.now()
				})
	
	@api.model
	def _action_sunat_exchange_rate(self):
		url = 'https://api.apis.net.pe/v1/tipo-cambio-sunat'
		try:
			res_html = urllib.request.urlopen(url)
			html = BeautifulSoup(res_html, "lxml")
			p = html.find("p")
			arr2 = json.loads(p.text.strip())
			currency = self.env.ref('base.USD')
			if arr2:
				'''
				values = {
					'compra': float(arr2["compra"]),
					'venta': float(arr2["venta"]),
				}
				'''
				buy = float(arr2["compra"])
				sale = float(arr2["venta"])
				rate_date = fields.Datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
				date_date = rate_date.date()
				self._update_rates(date_date,buy,sale,currency)
				#currency_rate = self.env['res.currency.rate']
				'''
				for cmpny in self.env['res.company'].search([]):
					rate = currency_rate.search([
						('currency_id', '=', currency.id),
						('name', '=', date_date),
						('company_id','=',cmpny.id)
					], limit=1)
					if not rate:
						currency_rate.create({
							'currency_id': currency.id,
							'rate': 1.0 / values['venta'],
							'name': rate_date,
							'sale_type': values['venta'],
							'purchase_type': values['compra'],
							'company_id': cmpny.id,
						})
					else:
						rate.write({
							'rate': 1.0 / values['venta'],
							'sale_type': values['venta'],
							'purchase_type': values['compra'],
						})
				'''
		except urllib.error.HTTPError as e:
			print('Error: %s' % e)
		except urllib.error.URLError as a:
			print('Error: %s' % a)
