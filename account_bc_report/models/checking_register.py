# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CheckingRegister(models.Model):
	_name = 'checking.register'
	_auto = False

	mayor = fields.Char(string='Mayor')
	cuenta = fields.Char(string='Cuenta')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')
	rubro = fields.Char(string='Rubro Estado Financiero')