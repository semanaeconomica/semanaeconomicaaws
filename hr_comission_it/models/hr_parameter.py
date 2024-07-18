# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	validator_comission_ids=fields.One2many('hr.comission.validator','parameter_id','Validadores')


class HrComissionValidator(models.Model):
	_name='hr.comission.validator'
	_description = 'Validadores de Comisiones'

	user_id = fields.Many2one('res.users','Usuario')
	first_validate = fields.Boolean(u'Primera Aprobación')
	second_validate = fields.Boolean(u'Segunda Aprobación')
	parameter_id = fields.Many2one('hr.main.parameter','Main')