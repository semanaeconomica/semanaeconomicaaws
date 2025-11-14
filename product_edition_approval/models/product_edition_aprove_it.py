# -*- coding: utf-8 -*-
from odoo import models, fields, api

class edition_aprov_level_it(models.Model):
	_name = 'edition.aprov.level.it'

	name   = fields.Char(u'Nivel de Apobación')
	order  = fields.Integer(u'Orden de Aplicación')
	user_id = fields.Many2one('res.users','Encargado')
	active = fields.Boolean('Activo')