# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CheckingBalance(models.Model):
	_name = 'checking.balance'
	_auto = False

	mayor = fields.Char(string='Mayor')
	nomenclatura = fields.Char(string='Nomenclatura')
	debe = fields.Float(string='Debe')
	haber = fields.Float(string='Haber')
	saldo_deudor = fields.Float(string='Saldo Deudor')
	saldo_acreedor = fields.Float(string='Saldo Acreedor')