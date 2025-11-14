# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountHigherBook(models.Model):
	_name = 'account.higher.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(12,2))
	saldo = fields.Float(string='Saldo', digits=(64,2))
	moneda = fields.Char(string='Mon', size=5)
	tc = fields.Float(string='TC', digits=(12,4))
	code_cta_analitica = fields.Char(string='Cta Analítica')
	glosa = fields.Char(string='Glosa',size=50)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC')
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=50)
	nro_comprobante = fields.Char(string=u'Nro Comprobante', size=50)
	fecha_doc = fields.Date(string=u'Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
