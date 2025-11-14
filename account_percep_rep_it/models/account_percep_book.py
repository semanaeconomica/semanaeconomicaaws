# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPercepBook(models.Model):
	_name = 'account.percep.book'
	_auto = False

	periodo_con = fields.Text(string='Periodo Con', size=50)
	periodo_percep = fields.Text(string='Periodo Percep', size=50)
	fecha_uso = fields.Date(string='Fecha Uso')
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	tipo_per = fields.Char(string='TDP',size=3)
	ruc_agente = fields.Char(string='RUC',size=50)
	partner = fields.Char(string='Partner')
	tipo_comp = fields.Char(string='TD')
	serie_cp = fields.Text(string='Serie', size=50)
	numero_cp = fields.Text(string='Numero', size=50)
	fecha_com_per = fields.Date(string='Fecha Com Per')
	percepcion = fields.Float(string='Percepcion',digits=(12,2))
	t_comp = fields.Char(string='T. Comp')
	serie_comp = fields.Text(string='Serie Comp', size=50)
	numero_comp = fields.Text(string='Numero Comp', size=50)
	fecha_cp = fields.Date(string='Fecha CP')
	montof = fields.Float(string='Monto',digits=(12,2))