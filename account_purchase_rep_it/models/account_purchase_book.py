# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPurchaseBook(models.Model):
	_name = 'account.purchase.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha_cont = fields.Date(string='Fecha Cont')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	fecha_e = fields.Date(string='Fecha Em')
	fecha_v = fields.Date(string='Fecha Ven')
	td = fields.Char(string='TD',size=3)
	serie = fields.Text(string='Serie', size=50)
	anio = fields.Char(string=u'Año')
	numero = fields.Text(string='Numero', size=50)
	tdp = fields.Char(string='TDP', size=50)
	docp = fields.Char(string='RUC',size=50)
	namep = fields.Char(string='Partner')
	base1 = fields.Float(string='BIOGYE',digits=(12,2))
	base2 = fields.Float(string='BIOGEYNG',digits=(12,2))
	base3 = fields.Float(string='BIONG',digits=(12,2))
	cng = fields.Float(string='CNG',digits=(12,2))
	isc = fields.Float(string='ISC',digits=(12,2))
	icbper = fields.Float(string='ICBPER',digits=(12,2))
	otros = fields.Float(string='Otros',digits=(12,2))
	igv1 = fields.Float(string='IGV 1',digits=(12,2))
	igv2 = fields.Float(string='IGV 2',digits=(12,2))
	igv3 = fields.Float(string='IGV 3',digits=(12,2))
	total = fields.Float(string='Total',digits=(12,2))
	name = fields.Char(string='Mon')
	monto_me = fields.Float(string='Monto Me',digits=(12,2))
	currency_rate = fields.Float(string='TC',digits=(12,4))
	fecha_det = fields.Date(string='Fecha Det')
	comp_det = fields.Char(string='Comp Det')
	f_doc_m = fields.Date(string='Fecha Doc M')
	td_doc_m = fields.Char(string='TD Doc M')
	serie_m = fields.Char(string='Serie M')
	numero_m = fields.Text(string='Numero M')
	glosa = fields.Char(string='Glosa')