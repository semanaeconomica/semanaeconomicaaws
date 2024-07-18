# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountTransferBook(models.Model):
	_name = 'account.transfer.book'
	_auto = False
	
	cuenta = fields.Char(string='Cuenta', size=64)
	debit = fields.Float(string='Debe', digits=(64,2))
	credit = fields.Float(string='Haber', digits=(64,2))
	cta_analitica = fields.Char(string=u'Cuenta Analítica')
