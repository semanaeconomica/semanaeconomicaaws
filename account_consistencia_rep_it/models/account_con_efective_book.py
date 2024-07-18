# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountConEfectiveBook(models.Model):
	_name = 'account.con.efective.book'
	_auto = False
	
	account_code = fields.Char(string='Cuenta')
	account_efective_type_name = fields.Char(string='Tipo Flujo de Efectivo')
	ingreso = fields.Float(string='Ingreso', digits=(64,2))
	egreso = fields.Float(string='Egreso', digits=(64,2))
	balance = fields.Float(string='Balance', digits=(64,2))