# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	fifth_afect_sr_id = fields.Many2one('hr.salary.rule', string='Rem. Ord. Afectas a Quinta', help='Remuneraciones Ordinarias Afectas Quinta')
	gratification_sr_id = fields.Many2one('hr.salary.rule', string='Gratificacion Julio y Diciembre')
	fifth_extr_sr_id = fields.Many2one('hr.salary.rule', string='Rem. Ext. de Quinta', help='Remuneraciones Extraordinarias de Quinta')
	fifth_category_input_id = fields.Many2one('hr.payslip.input.type', string='Input Quinta Categoria')
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal')
	rate_limit_ids = fields.One2many('hr.rate.limit', 'main_parameter_id')

	def check_fifth_values(self):
		if not self.fifth_afect_sr_id or \
		   not self.gratification_sr_id or \
		   not self.fifth_extr_sr_id or \
		   not self.fifth_category_input_id or \
		   not self.rate_limit_ids or \
		   not self.fiscal_year_id.uit > 0:
		   raise UserError(u'Faltan Configuraciones en la Pestaña de Quinta del Menu de Parametros Principales')

class HrRateLimit(models.Model):
	_name = 'hr.rate.limit'
	_description = 'Rate Limit'

	main_parameter_id = fields.Many2one('hr.main.parameter', ondelete='cascade')
	range = fields.Integer(string='Rango')
	limit = fields.Integer(string='Limite')
	rate = fields.Integer(string='Tasa')