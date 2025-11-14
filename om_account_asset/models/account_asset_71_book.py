# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAsset71Book(models.Model):
	_name = 'account.asset.71.book'
	_auto = False
	
	campo1 = fields.Char(string=u'Código Relacionado con el Activo Fijo', size=50)
	campo2 = fields.Char(string=u'Cuenta Contable del Activo Fijo', size=50)
	campo3 = fields.Char(string=u'Descripción')
	campo4 = fields.Char(string=u'Marca del Activo Fijo')
	campo5 = fields.Char(string=u'Modelo del Activo Fijo')
	campo6 = fields.Char(string=u'Número de Serie y/o Placa del Activo Fijo')
	campo7 = fields.Float(string=u'Saldo Inicial',digits=(12,2))
	campo8 = fields.Float(string=u'Adquisiones Adiciones',digits=(12,2))
	campo9 = fields.Float(string=u'Mejoras',digits=(12,2))
	campo10 = fields.Float(string=u'Retiros y/o Bajas',digits=(12,2))
	campo11 = fields.Float(string=u'Otros Ajustes',digits=(12,2))
	campo12 = fields.Float(string=u'Valor Histórico del Activo Fijo al 31.12',digits=(12,2))
	campo13 = fields.Float(string=u'Ajuste por Inflación',digits=(12,2))
	campo14 = fields.Float(string=u'Valor Ajustado del Activo Fijo al 31.12',digits=(12,2))
	campo15 = fields.Date(string=u'Fecha de Adquisición')
	campo16 = fields.Date(string=u'Fecha Inicio del Uso del Activo Fijo')
	campo17 = fields.Char(string=u'Método Aplicado')
	campo18 = fields.Char(string=u'Nro de Documento de Autorización')
	campo19 = fields.Float(string=u'Porcentaje de Depreciación',digits=(12,2))
	campo20 = fields.Float(string=u'Depreciación acumulada al Cierre del Ejercicio Anterior',digits=(12,2))
	campo21 = fields.Float(string=u'Depreciación del Ejercicio',digits=(12,2))
	campo22 = fields.Float(string=u'Depreciación del Ejercicio Relacionada con los retiros y/o bajas',digits=(12,2))
	campo23 = fields.Float(string=u'Depreciación relacionada con otros ajustes',digits=(12,2))
	campo24 = fields.Float(string=u'Depreciación acumulada Histórico',digits=(12,2))
	campo25 = fields.Float(string=u'Ajuste por inflación de la Depreciación',digits=(12,2))
	campo26 = fields.Float(string=u'Depreciación acumulada Ajustada por Inflación',digits=(12,2))