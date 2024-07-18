# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBalanceDetailBook(models.Model):
	_name = 'account.balance.detail.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Date(string='Fecha')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=3)
	nro_comprobante = fields.Char(string='Nro Comp', size=50)
	fecha_doc = fields.Date(string='Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	cuenta = fields.Char(string='Cuenta')
	moneda = fields.Char(string='Moneda')
	debe = fields.Float(string='Debe', digits=(64,2))
	haber = fields.Float(string='Haber', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(64,2))
	importe_me = fields.Float(string='Importe Me', digits=(64,2))
	saldo = fields.Float(string='Saldo Mn', digits=(64,2))
	saldo_me = fields.Float(string='Saldo Me', digits=(64,2))