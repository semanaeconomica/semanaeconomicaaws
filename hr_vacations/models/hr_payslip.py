# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	accrual_vacation_ids = fields.One2many('hr.accrual.vacation', 'slip_id')

class HrAccrualVacation(models.Model):
	_name = 'hr.accrual.vacation'
	_description = 'Accrual Vacation'

	slip_id = fields.Many2one('hr.payslip', string='Nomina', ondelete='cascade')
	accrued_period = fields.Many2one('hr.payslip.run', string='Periodo Devengue')
	days = fields.Integer(string='Dias de Vacaciones')
	employee_id = fields.Many2one(related='slip_id.employee_id', string='Empleado')