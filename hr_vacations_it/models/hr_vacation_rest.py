from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class HrVacationRest(models.Model):
	_name='hr.vacation.rest'
	_description='Saldos de Vacaciones'

	employee_id=fields.Many2one('hr.employee','Empleado')
	date_from= fields.Date('Periodo')
	date_end= fields.Date('Periodo fin')
	internal_motive= fields.Selection([('rest','Saldo anterior'),('normal','Vacaciones')],'Motivo Interno',default='normal')
	motive = fields.Char('Motivo')
	days = fields.Integer(u'Días')
	days_rest = fields.Integer(u'Saldo en días')
	year = fields.Char(u'Año')

	def get_vacation_employee(self,year,employee,show_all):
		self.search([('internal_motive','=','normal')]).unlink()
		if show_all:
			employes = self.env['hr.employee'].search([])
		else:
			employes = [employee]
		for employee in employes:
			last_contract = self.env['hr.contract'].search([('employee_id','=',employee.id),
						('labor_regime','in',['general','small']),('state', 'in', ['open'])])
			if len(last_contract)>1:
				name=employee.names+' '+employee.last_name+' '+employee.m_last_name
				raise ValidationError('El empleado %s tiene dos contratos activos' % name)
			act_date = datetime.now()
			date_time_str=year+'-01-01 00:00:00'
			date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
			vals={
				'employee_id':employee.id,
				'date_from':date_time_obj.date(),
				'date_end':date_time_obj.date(),
				'internal_motive':'normal',
				'motive':'Vacaciones Devengadas',
				'days':30,
				'days_rest':30,
				'year':year
			}
			self.create(vals)
			AccrualVacations = self.env['hr.accrual.vacation'].search([('employee_id', '=', employee.id)]) 
			if AccrualVacations:
				AccrualVacations = AccrualVacations.sorted(key=lambda a_vacation:a_vacation.accrued_period.date_start)
				for a_vacation in AccrualVacations:
					if a_vacation.accrued_period.date_start.year==int(year):
						vals={
							'employee_id':employee.id,
							'date_from':a_vacation.slip_id.date_from,
							'date_end':a_vacation.slip_id.date_to,
							'internal_motive':'normal',
							'motive':'Vacaciones tomadas',
							'days':a_vacation.days*-1,
							'days_rest':None,
							'year':year
						}
						self.create(vals)

			vacas = self.search([('employee_id','=',employee.id)])
			vacas_sorted=vacas.sorted(key=lambda avacas:avacas.date_end)
			saldo=0
			for vaca in vacas_sorted:
				if saldo==0:
					saldo = vaca.days
					continue
				else:
					saldo = saldo+vaca.days
				vaca.days_rest=saldo










