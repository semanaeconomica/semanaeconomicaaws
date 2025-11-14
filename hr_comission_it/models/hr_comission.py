# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from copy import copy
import babel
import base64

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

class HrComission(models.Model):
	_name = 'hr.comission'
	_description = 'Comisiones y Bonos'

	name = fields.Char(string='Nombre', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	state = fields.Selection([
		('draft','Borrador'),
		('wait',u'Primera aprobación'),
		('secondapprove',u'Segunda aprobación'),
		('approve','Aprobada'),
		('refuse','Rechazada'),
		('payed','En planilla'),
		('cancel','Cancelada')], 
		string='Estado', default='draft',copy=False)
	input_id = fields.Many2one('hr.payslip.input.type',u'Tipo de entrada en Nómina')
	amount = fields.Float('Monto',digits=(12,2),copy=False)
	employee_id = fields.Many2one('hr.employee','Empleado')
	payslip_id = fields.Many2one('hr.payslip','Nómina')
	user_approve_id = fields.Many2one('res.users','Usuario que aprueba',copy=False)
	user_refuse_id = fields.Many2one('res.users','Usuario que rechaza',copy=False)
	date_approve = fields.Date(u'Fecha de aprobación',copy=False)
	date_refuse = fields.Date(u'Fecha de rechazo',copy=False)
	motive = fields.Text('Comentario',copy=False)


	@api.onchange('employee_id')
	def onchange_employee_id(self):
		res={}
		res['domain']={'payslip_id':[('employee_id','=',self.employee_id.id)]}
		return res


	@api.model
	def create(self,vals):
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('comission.seq') or _('New')
		return super(HrComission,self).create(vals)



	def make_wait(self):
		for l in self:
			l.state = 'wait'

	# def approve(self):
	# 	MainParameter = self.env['hr.main.parameter'].get_main_parameter()
	# 	c=MainParameter.validator_comission_ids.filtered(lambda validator:validator.user_id==self.env.user)
	# 	if c:
	# 		for l in self:
	# 			l.user_approve_id = self.env.user.id
	# 			l.date_approve = fields.Date.today()
	# 			l.state = 'approve'
	# 	else:
	# 		raise ValidationError('No tiene permiso para aprobar')		




	def action_approve(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		valida1 = False
		valida2 = False
		first_validators=[]
		second_validators=[]
		res=False
		for l in MainParameter.validator_comission_ids:
			if self.env.user.id == l.user_id.id:
				if l.first_validate:
					valida1=l.first_validate
				if l.second_validate:
					valida2=l.second_validate
			if l.first_validate:
				first_validators.append(l.user_id.id)
			if l.second_validate:
				second_validators.append(l.user_id.id)
		if not valida1:
			raise UserError(u'No tiene permiso para realizar esta operación')
		else:
			print(first_validators)
			if self.env.user.id in first_validators:
				self.user_approve_id = self.env.user.id
				self.date_approve = fields.Date.today()
				self.state = 'secondapprove'
			else:
				raise UserError(u'No tiene permiso para realizar esta operación')
		return res						

	def action_approve2(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		valida1 = False
		valida2 = False
		first_validators=[]
		second_validators=[]
		res=False
		for l in MainParameter.validator_comission_ids:
			if self.env.user.id == l.user_id.id:
				if l.first_validate:
					valida1=l.first_validate
				if l.second_validate:
					valida2=l.second_validate
			if l.first_validate:
				first_validators.append(l.user_id.id)
			if l.second_validate:
				second_validators.append(l.user_id.id)
		if not valida2:
			raise UserError(u'No tiene permiso para realizar esta operación')
		else:
			if self.env.user.id in second_validators:
				self.user_approve_id = self.env.user.id
				self.date_approve = fields.Date.today()
				self.state = 'approve'
			else:
				raise UserError(u'No tiene permiso para realizar esta operación')
		return res						

	def make_cancel(self):
		for l in self:
			if l.state not in ('payed'):
				l.user_refuse_id = None
				l.date_refuse = None
				l.user_approve_id = None
				l.date_approve = None
				l.state = 'cancel'
			else:
				raise ValidationError('No se puede cancelar si se encuentra aprobada o en planilla')		
	def refuse(self):
		for l in self:
			if l.state in ('wait,secondapprove'):
				l.user_refuse_id = self.env.user.id
				l.date_refuse = fields.Date.today()
				l.state = 'refuse'			
			else:
				raise ValidationError('No se puede rechazar ya que se encuentra pagada ')

	def send_payslip(self):
		for l in self:
			if l.state in ('approve'):
				c=l.payslip_id.input_line_ids.filtered(lambda input:input.input_type_id==l.input_id)
				if c:
					c.amount = l.amount
				l.state = 'payed'


	def send_to_draft(self):
		for l in self:
			l.user_refuse_id = None
			l.date_refuse = None
			l.user_approve_id = None
			l.date_approve = None
			l.state='draft'