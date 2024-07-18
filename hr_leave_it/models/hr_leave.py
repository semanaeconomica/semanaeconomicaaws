# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from collections import namedtuple


class hr_work_suspension(models.Model):
	_inherit='hr.work.suspension'

	leave_id = fields.Many2one('hr.leave','Ausencia')

class hr_accrual_vacation(models.Model):
	_inherit='hr.accrual.vacation'

	leave_id = fields.Many2one('hr.leave','Ausencia')

class HrLeaveAllocation(models.Model):
	_inherit = 'hr.leave.allocation'

	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	contract_id = fields.Many2one('hr.contract','Contrato')
	comment_to_eployee = fields.Text('Nota para el empleado')
	comment_from_eployee = fields.Text('Comentario del empleado')
	leave_type_id = fields.Many2one('hr.leave.type.it','Tipo de ausencia')

	leave_motive_id = fields.Many2one('hr.leave.motive.it',u'Modo de Asignación')	



class HrLeave(models.Model):
	_inherit = 'hr.leave'

	contract_id = fields.Many2one('hr.contract','Contrato')
	leave_type_id = fields.Many2one('hr.leave.type.it','Tipo de ausencia')
	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	leave_motive_id = fields.Many2one('hr.leave.motive.it',u'Modo de Asignación')
	comment_to_eployee = fields.Text('Nota para el empleado')
	comment_from_eployee = fields.Text('Comentario del empleado')
	work_suspension_id = fields.Many2one('hr.suspension.type', u'Tipo de Suspensión')


	employee_id = fields.Many2one(
		'hr.employee', string='Employee', index=True, readonly=True, ondelete="restrict",
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, tracking=True)
	
	department_id = fields.Many2one(
		'hr.department', string='Department', readonly=True,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

	def _get_number_of_days(self, date_from, date_to, employee_id):
		if employee_id:
			employee = self.env['hr.employee'].browse(employee_id)
			return {'days': (date_to-date_from).days+1, 'hours': 0}
		return {'days': (date_to-date_from).days+1, 'hours': 0}


	@api.model
	def default_get(self, fields_list):
		defaults = super(HrLeave, self).default_get(fields_list)
		defaults = self._default_get_request_parameters(defaults)
		LeaveType = self.env['hr.leave.type'].with_context(employee_id=defaults.get('employee_id'), default_date_from=defaults.get('date_from', fields.Datetime.now()))
		lt = LeaveType.search([('valid', '=', True)], limit=1)
		defaults['holiday_status_id'] = lt.id if lt else defaults.get('holiday_status_id')
		defaults['state'] = 'confirm' if lt and lt.validation_type != 'no_validation' else 'draft'
		return defaults

	@api.onchange('contract_id')
	def onchange_contract(self):
		if self.contract_id.id:
			self.employee_id = self.contract_id.employee_id.id
			self.department_id = self.contract_id.employee_id.department_id.id
		else:
			self.employee_id=None
			self.department_id = None


	# @api.onchange('holiday_type')
	# def _onchange_type(self):
	# 	if self.holiday_type == 'employee':
	# 		if not self.employee_id:
	# 			self.employee_id = self.env.user.employee_id.id
	# 		self.mode_company_id = False
	# 		self.category_id = False
	# 	return True

	def action_refuse(self):
		l = self.contract_id.work_suspension_ids.filtered(lambda reg: reg.leave_id.id == self.id)
		h = self.env['hr.accrual.vacation'].search([('leave_id','=',self.id)])
		if self.payslip_status or len(l)>0 or len(h)>0:
			raise UserError(u'No se puede rechazar si ya se encuentra en reportado en planilla')
		super(HrLeave,self).action_refuse()

	def action_approve(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		valida1 = False
		valida2 = False
		first_validators=[]
		second_validators=[]
		res=False
		for l in MainParameter.validator_ids:
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
			if self.env.user.id in first_validators:
				res = super(HrLeave,self).action_approve()
			else:
				raise UserError(u'No tiene permiso para realizar esta operación')
		return res


		

	def action_validate(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		valida1 = False
		valida2 = False
		first_validators=[]
		second_validators=[]
		res=False
		for l in MainParameter.validator_ids:
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

				res = super(HrLeave,self).action_validate()

			else:
				raise UserError(u'No tiene permiso para realizar esta operación')
		return res



	def prepare_suspension_data(self,contract_id,MainParameter):
		vals={
			'suspension_type_id':self.work_suspension_id.id,
			'reason':MainParameter.motive_text,
			'days':self.number_of_days,
			'payslip_run_id':self.payslip_run_id.id,
			'leave_id':self.id,
			'contract_id':contract_id.id,
		}		
		return vals
	def prepare_payslip_data(self,slip):
		vals={
			'days':self.number_of_days,
			'accrued_period':self.payslip_run_id.id,
			'leave_id':self.id,
			'slip_id':slip.id,
		}		
		return vals	

	def send_data_to_payslip(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for l in self:

			if l.payslip_status == False:
				if l.state=='validate':
					slip = self.env['hr.payslip'].search([('payslip_run_id','=',l.payslip_run_id.id),('employee_id','=',l.employee_id.id)])
					if len(slip)==0:
						raise UserError(u'El empleado seleccionado no existe en la nómina de ese periodo')
					vals = l.prepare_suspension_data(slip.contract_id,MainParameter)
					self.env['hr.work.suspension'].create(vals)
					if l.work_suspension_id.id == MainParameter.suspension_type_id.id:
						vals=l.prepare_payslip_data(slip)
						self.env['hr.accrual.vacation'].create(vals)	
					l.payslip_status = True



	@api.model_create_multi
	def create(self, vals_list):
		for l in vals_list:
			c = self.env['hr.contract'].browse(l['contract_id'])
			l['employee_id']=c.employee_id.id

		holidays = super(HrLeave, self.with_context(mail_create_nosubscribe=True,leave_fast_create=True)).create(vals_list)
		return holidays

	@api.constrains('state', 'number_of_days', 'holiday_status_id')
	def _check_holidays(self):
		mapped_days = self.mapped('holiday_status_id').get_employees_days(self.mapped('employee_id').ids)
		for holiday in self:
			continue
	
	def _sync_employee_details(self):
		for holiday in self:
			holiday.manager_id = holiday.employee_id.parent_id.id
			if holiday.employee_id:
				holiday.department_id = holiday.employee_id.department_id


	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		self._sync_employee_details()

class HrLeaveTypeIt(models.Model):
	_name = 'hr.leave.type.it'
	_description = u'Tipo de Ausencia'

	name=fields.Char('Tipo de Ausencia')
	is_vacation=fields.Boolean('Vacaciones')


class HrLeaveMotiveIt(models.Model):
	_name = 'hr.leave.motive.it'
	_description = u'Motivo de Asignación'

	name = fields.Char(u'Motivo de Asignación')



class LeaveReport(models.Model):
	_inherit = "hr.leave.report"	


	work_suspension_id = fields.Many2one('hr.suspension.type', u'Tipo de Suspensión')


	def init(self):
		tools.drop_view_if_exists(self._cr, 'hr_leave_report')

		self._cr.execute("""
			CREATE or REPLACE view hr_leave_report as (
				SELECT row_number() over(ORDER BY leaves.employee_id) as id,
				leaves.employee_id as employee_id, leaves.name as name,
				leaves.number_of_days as number_of_days, leaves.leave_type as leave_type,
				leaves.category_id as category_id, leaves.department_id as department_id,
				leaves.holiday_status_id as holiday_status_id, leaves.state as state,
				leaves.holiday_type as holiday_type, leaves.date_from as date_from,
				leaves.date_to as date_to, leaves.payslip_status as payslip_status,
				leaves.work_suspension_id as work_suspension_id
				from (select
					allocation.employee_id as employee_id,
					allocation.name as name,
					allocation.number_of_days as number_of_days,
					allocation.category_id as category_id,
					allocation.department_id as department_id,
					allocation.holiday_status_id as holiday_status_id,
					allocation.state as state,
					allocation.holiday_type,
					null as date_from,
					null as date_to,
					FALSE as payslip_status,
					'allocation' as leave_type,
					null as work_suspension_id
				from hr_leave_allocation as allocation
				union all select
					request.employee_id as employee_id,
					request.name as name,
					(request.number_of_days * -1) as number_of_days,
					request.category_id as category_id,
					request.department_id as department_id,
					request.holiday_status_id as holiday_status_id,
					request.state as state,
					request.holiday_type,
					request.date_from as date_from,
					request.date_to as date_to,
					request.payslip_status as payslip_status,
					'request' as leave_type,
					request.work_suspension_id as work_suspension_id
				from hr_leave as request) leaves
			);
		""")
