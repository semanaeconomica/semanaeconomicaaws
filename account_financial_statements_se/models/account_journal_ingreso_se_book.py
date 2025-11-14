# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournalIngresoSeBook(models.Model):
	_name = 'account.journal.ingreso.se.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	fecha = fields.Text(string='Fecha', size=15)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	cuenta = fields.Char(string='Cuenta', size=64)
	balance = fields.Float(string='Balance', digits=(12,2))
	moneda = fields.Char(string='Mon', size=5)
	tc = fields.Float(string='TC', digits=(12,4))
	importe_me = fields.Float(string='Importe Me',digits=(64,2))
	code_cta_analitica = fields.Char(string=u'Categoría de Venta')
	glosa = fields.Char(string='Glosa',size=50)
	td_partner = fields.Char(string='TDP', size=50)
	doc_partner = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	td_sunat = fields.Char(string='TD',size=50)
	nro_comprobante = fields.Char(string=u'Nro Comp', size=50)
	fecha_doc = fields.Date(string=u'Fecha Doc')
	fecha_ven = fields.Date(string='Fecha Ven')
	canje = fields.Char(string='Canje')