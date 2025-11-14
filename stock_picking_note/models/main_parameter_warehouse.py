# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class MainParameterWarehouse(models.Model):
	_name = 'main.parameter.warehouse'

	name = fields.Char(default='Parametros Principales')

	albaran_limit_line = fields.Integer(string=u'Límite de líneas de Albarán')
	date_albaran_validate = fields.Boolean(string=u'Validar fecha de albarán')




