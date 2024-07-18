# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountFeeBook(models.Model):
	_name = 'account.fee.book'
	_auto = False
	
	periodo = fields.Text(string='Periodo', size=50)
	libro = fields.Char(string='Libro', size=5)
	voucher = fields.Char(string='Voucher', size=10)
	fecha_e = fields.Date(string='Fecha E')
	fecha_p = fields.Date(string='Fecha P')
	td = fields.Char(string='TD',size=3)
	serie = fields.Text(string='Serie', size=50)
	numero = fields.Text(string='Numero', size=50)
	tdp = fields.Char(string='TDP', size=50)
	docp = fields.Char(string='RUC',size=50)
	apellido_p = fields.Char(string='Ap. Paterno')
	apellido_m = fields.Char(string='Ap. Materno')
	namep = fields.Char(string='Nombres')
	divisa = fields.Char(string='Divisa')
	tipo_c = fields.Float(string='TC',digits=(12,4))
	renta = fields.Float(string='Renta',digits=(12,2))
	retencion = fields.Float(string='Retencion',digits=(12,2))
	neto_p = fields.Float(string='Neto P',digits=(12,2))
	periodo_p = fields.Text(string='Periodo P', size=50)
	is_not_home = fields.Char(string='No Domiciliado',size=1)
	c_d_imp = fields.Char(string='Conv. Evit. Doble Imp.')
