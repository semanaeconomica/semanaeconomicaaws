# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	validator_ids=fields.One2many('hr.leave.validator','parameter_id','Validadores')
	suspension_type_id = fields.Many2one('hr.suspension.type',u'Tipo de Suspensión')
	motive_text = fields.Char('Texto para el motivo',default='Vacaciones')


class HrLeaveValidator(models.Model):
	_name='hr.leave.validator'
	_description = 'Validadores de Vacaciones'

	user_id = fields.Many2one('res.users','Usuario')
	first_validate = fields.Boolean(u'Primera Aprobación')
	second_validate = fields.Boolean(u'Segunda Aprobación')
	parameter_id = fields.Many2one('hr.main.parameter','Main')