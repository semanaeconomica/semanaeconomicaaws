# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MaturityAnalysisBook(models.Model):
	_name = 'maturity.analysis.book'
	_auto = False

	fecha_emi = fields.Date(string='Fecha Emi.')
	fecha_ven = fields.Date(string='Fecha Ven.')
	cuenta = fields.Char(string='Cuenta')
	divisa = fields.Char(string='Divisa', size=10)
	tdp = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')	
	td_sunat = fields.Char(string='TD',size=50)
	nro_comprobante = fields.Text(string='Nro Comp', size=50)
	saldo_mn = fields.Float(string='Saldo MN',digits=(12,2))
	saldo_me = fields.Float(string='Saldo ME',digits=(12,2))
	cero_treinta = fields.Float(string='0 - 30',digits=(12,2))
	treinta1_sesenta = fields.Float(string='31 - 60',digits=(12,2))
	sesenta1_noventa = fields.Float(string='61 - 90',digits=(12,2))
	noventa1_ciento20 = fields.Float(string='91 - 120',digits=(12,2))
	ciento21_ciento50 = fields.Float(string='121 - 150',digits=(12,2))
	ciento51_ciento80 = fields.Float(string='151 - 180',digits=(12,2))
	ciento81_mas = fields.Float(string=u'181 - Más',digits=(12,2))