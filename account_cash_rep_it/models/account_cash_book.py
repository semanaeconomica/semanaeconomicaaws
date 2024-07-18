# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountCashBook(models.Model):
	_name = 'account.cash.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	debe = fields.Float(string='Debe', digits=(64,2))
	debe_me = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	haber_me = fields.Float(string='Haber', digits=(64,2))
	saldo = fields.Float(string='Saldo Mn', digits=(64,2))
	moneda = fields.Char(string='Moneda', size=5)
	tc = fields.Float(string='Tipo Cambio', digits=(12,4))
	saldo_me = fields.Float(string='Saldo Me', digits=(64,2))
	code_cta_analitica = fields.Char(string='Cuenta Analítica')
	glosa = fields.Char(string='Glosa',size=50)
	td_partner = fields.Char(string='Tipo de Documento', size=50)
	doc_partner = fields.Char(string='RUC')
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='Tipo Documento Sunat',size=50)
	nro_comprobante = fields.Char(string=u'Número de Comprobante', size=50)
	fecha_doc = fields.Date(string=u'Fecha Documento')
	fecha_ven = fields.Date(string='Fecha Vencimiento')
