# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2013-2014 Agustin Cruz openpyme.mx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface
from odoo import fields
from datetime import datetime
import pytz
import re
import requests
import urllib.request
import sys
from bs4 import BeautifulSoup as BS
import calendar
import logging
_logger = logging.getLogger(__name__)


class PeSunatGetter(CurrencyGetterInterface):
	"""Implementation of Currency_getter_factory interface
	for SUNAT service

	"""
	code = 'PE_SUNAT'
	name = 'Superintendencia Nacional de Aduanas y de Administración Tributaria'
	supported_currency_array = [
		"PEN", "USD"]

	def rate_retrieve(self, date = None):
		""" Get currency exchange from Banxico.xml and proccess it
		TODO: Get correct data from xml instead of process string
		"""
		if not date:
			today = datetime.now()
			tz_name = "America/Lima"
			today_utc = pytz.timezone('UTC').localize(today, is_dst=False)
			context_today = today_utc.astimezone(pytz.timezone(tz_name))
			date = fields.Date.to_string(context_today)
		anho = date[:4]
		day = date[8:10]
		#if day == '01':
		#    mes = str(int(date[5:7])-1).zfill(2)
		#    if mes == '00':
		#        mes = '12'
		#        anho = str(int(anho)-1)
		#    day = calendar.monthrange(int(anho),int(mes))[1]
		#else:
		mes = date[5:7]
		diccionario = self.get_dictionary(mes, anho)
		while True and int(day) > 0:
			if str(int(day)) in diccionario.keys():
				compra = diccionario.get(str(int(day))).get('compra',0)
				venta = diccionario.get(str(int(day))).get('venta',0)
				break
			else:
				day = str(int(day)-1)
				if int(day) == 0:
					mes = str(int(date[5:7])-1).zfill(2)
					if mes == '00':
						mes = '12'
						anho = str(int(anho)-1)
					day = str(calendar.monthrange(int(anho),int(mes))[1])
					diccionario = self.get_dictionary(mes, anho)

		rates = {'USD':{'currency_code':'02','description':'Dolar de N.A.','name':'USD','purchase_value': compra,'sale_value':venta}}
		return rates

	def get_dictionary(self, mes, anho):
		url = ('https://e-consulta.sunat.gob.pe/cl-at-ittipcam/tcS01Alias?mes=%s&anho=%s' %(mes,anho))
		req = urllib.request.Request(url)
		req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9')
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')
		usock = urllib.request.urlopen(req)
		data = usock.read()
		usock.close()
		soup = BS(data)
		dias = soup.find_all('td', {'class':'H3'})
		todos = soup.find_all('td', {'class':'tne10'})
		diccionario = {}
		comven = 0
		for dia in dias:
			diccionario.update({str(int(dia.text)): {'compra': float(todos[comven].text), 'venta': float(todos[comven + 1].text)}})
			comven += 2
		return diccionario

	def get_updated_currency(self, currency_array, main_currency,
							 max_delta_days=1, date = None):
		"""implementation of abstract method of Curreny_getter_interface"""
		logger = logging.getLogger(__name__)
		# we do not want to update the main currency
		if main_currency in currency_array:
			currency_array.remove(main_currency)

		# Suported currencies
		suported = ['USD']
		rates = self.rate_retrieve(date)
		for curr in currency_array:
			if curr in suported:
				rate = rates.get(curr)
				if rate:
					rate['purchase_value'] = rates.get(curr).get('purchase_value') or 0
					rate['sale_value'] =  rates.get(curr).get('sale_value') or 0
					self.updated_currency[curr] =rates.get(curr)
			else:
				# No other currency supported
				continue
			logger.debug("Rate retrieved : %s = %s %s" %
						 (main_currency, str(rates), curr))
		return self.updated_currency, self.log_info
