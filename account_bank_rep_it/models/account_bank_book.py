# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankBook(models.Model):
	_name = 'account.bank.book'
	_auto = False
	
	fecha = fields.Date(string='Fecha')
	partner = fields.Char(string='Partner')
	documento = fields.Char(string='Documento')
	glosa = fields.Char(string='Glosa')
	cargomn = fields.Float(string='Cargo MN',digits=(64,2))
	abonomn = fields.Float(string='Abono MN',digits=(64,2))
	saldomn = fields.Float(string='Saldo MN',digits=(64,2))
	cargome = fields.Float(string='Cargo ME',digits=(64,2))
	abonome = fields.Float(string='Abono ME',digits=(64,2))
	saldome = fields.Float(string='Saldo ME',digits=(64,2))
	asiento = fields.Char(string='Nro Asiento')