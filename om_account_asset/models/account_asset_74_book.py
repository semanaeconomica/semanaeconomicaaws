# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAsset71Book(models.Model):
	_name = 'account.asset.74.book'
	_auto = False
	
	campo1 = fields.Char(string=u'Activo Fijo')
	campo2 = fields.Date(string=u'Fecha del Contrato')
	campo3 = fields.Char(string=u'Nro del Contrato de Arrendamiento')
	campo4 = fields.Date(string=u'Fecha del Inicio del Contrato')
	campo5 = fields.Integer(string=u'Nro de Cuotas Pactadas')
	campo6 = fields.Float(string=u'Monto del Contrato',digits=(12,2))