# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountProjectedCashFlowBook(models.Model):
	_name = 'account.projected.cash.flow.book'

	grupo = fields.Char(string='Grupo')
	concepto = fields.Char(string='Concepto')
	account_id = fields.Many2one('account.account',string='Cuenta')
	fecha = fields.Date(string=u'Fecha V.')
	amount = fields.Float(string='Movimiento', digits=(64,2))
	anio = fields.Char(string=u'Año')
	mes = fields.Char(string='MES')
	user_id = fields.Many2one('res.users',string='Usuario')