# -*- coding:utf-8 -*-
from datetime import date, datetime, time
from odoo import api, fields, models

class HrContract(models.Model):
	_inherit = 'hr.contract'

	fifth_rem_proyected = fields.Float(string='Remuneracion Afecta Quinta Proyectada')
	grat_july_proyected = fields.Float(string='Gratificacion de Julio Proyectada')
	grat_december_proyected = fields.Float(string='Gratificacion de Diciembre Proyectada')