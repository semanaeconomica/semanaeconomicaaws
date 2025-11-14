# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAssetBook(models.Model):
	_name = 'account.asset.book'
	_auto = False
	
	code = fields.Char(string='Codigo', size=50)
	name = fields.Char(string='Activo', size=150)
	mes = fields.Integer(string='Mes')
	period = fields.Text(string='Periodo', size=10)
	cat_name = fields.Char(string=u'Categoría', size=100)
	cta_analitica = fields.Char(string='Cta. Analitica')
	eti_analitica = fields.Char(string='Etiqueta Analitica')
	cta_activo = fields.Char(string='Cta. Activo')
	cta_gasto = fields.Char(string='Cta. Gasto')
	cta_depreciacion = fields.Char(string='Cta Depreciacion')
	valor_dep = fields.Float(string=u'Valor de Depreciación',digits=(12,2))