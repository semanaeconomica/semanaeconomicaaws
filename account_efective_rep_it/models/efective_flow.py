# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EfectiveFlow(models.Model):
	_name = 'efective.flow'
	_auto = False
	_order = 'efective_order'

	name = fields.Char(string='Nombre')
	efective_group = fields.Char(string='Grupo')
	total = fields.Float(string='Total')
	efective_order = fields.Integer(string='Orden')

class DynamicEfectiveFlow(models.Model):
	_name = 'dynamic.efective.flow'

	name = fields.Char()