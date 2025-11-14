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

class HrVacationControl(models.Model):
	_name = 'hr.vacation.control'
	_description = 'Vacation Control'

	name = fields.Char(string='Nombre')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	state = fields.Selection([('generated','Generada'),('closed','Cerrada')], string='Estado', default='generated')
	vacation_line_ids = fields.One2many('hr.vacation.control.line', 'vacation_control_id')

	@api.model
	def create(self, vals):
		if self.env['hr.vacation.control'].search([('company_id', '=', self.env.company.id)]):
			raise UserError('No se puede crear mas de un Control de Vacaciones para esta compañia')
		else:
			return super(HrVacationControl, self).create(vals)

	def cerrar(self):
		self.state = 'closed'

	def reabrir(self):
		self.state = 'generated'

	def unlink(self):
		for i in self.ids:
			self.env['hr.vacation.control.line'].search([('vacation_control_id', '=', i)]).unlink()
		return super(HrVacationControl,self).unlink()

	def get_vacation(self):
		if self.vacation_line_ids:
			self.vacation_line_ids.unlink()
		employees = self.env['hr.employee'].search([('id', '!=', '1')])
		for employee in employees:
			saldo, aux_year = 30, 0
			AccrualVacations = self.env['hr.accrual.vacation'].search([('employee_id', '=', employee.id)])
			if AccrualVacations:
				AccrualVacations = AccrualVacations.sorted(key=lambda a_vacation:a_vacation.accrued_period.date_start)
				for a_vacation in AccrualVacations:
					year = self.env['account.fiscal.year'].search([('name', '=', a_vacation.accrued_period.date_start.year)], limit=1)
					if year != aux_year:
						saldo = 30
					aux_year = year
					if a_vacation.days > 0:
						self.env['hr.vacation.control.line'].create({
							'fiscal_year_id': year.id,
							'identification_id': employee.identification_id,
							'employee_id': employee.id,
							'payroll_period': a_vacation.slip_id.payslip_run_id.id,
							'accrued_period': a_vacation.accrued_period.id,
							'vacation_balance': saldo,
							'expended_days':  a_vacation.days,
							'total': saldo - a_vacation.days,
							'vacation_control_id': self.id
						})
						saldo = saldo - a_vacation.days
				if saldo == 30:
					self.env['hr.vacation.control.line'].create({
							'fiscal_year_id': 0,
							'identification_id': employee.identification_id,
							'employee_id': employee.id,
							'payroll_period': 0,
							'accrued_period': 0,
							'vacation_balance': saldo,
							'expended_days': 0,
							'total': saldo,
							'vacation_control_id': self.id
						})
		return self.env['popup.it'].get_message('Se actualizo correctamente')

	def get_excel_vacation(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file
		if not route:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		workbook = Workbook(route + 'control_vacaciones.xlsx')
		worksheet = workbook.add_worksheet("Vacaciones")
		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)
		
		import importlib
		import sys
		importlib.reload(sys)

		worksheet.merge_range(1, 0, 1, 7, "CONTROL DE VACACIONES", formats['especial3'])
		HEADERS = ["AÑO", "DNI", "APELLIDOS Y NOMBRES", "PERIODO PLANILLA", "PERIODO DEVENGUE", "SALDO VACACIONES", "DIAS GOZADOS", "TOTAL"]
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 4, 0, formats['boldbord'])

		x = 5
		for line in self.vacation_line_ids:
			worksheet.write(x,0,line.fiscal_year_id.name if line.fiscal_year_id else '', formats['especial1'])
			worksheet.write(x,1,line.identification_id if line.identification_id else '', formats['especial1'])
			worksheet.write(x,2,line.employee_id.name, formats['especial1'])
			worksheet.write(x,3,line.payroll_period.name if line.payroll_period else '', formats['especial1'])
			worksheet.write(x,4,line.accrued_period.name if line.accrued_period else '', formats['especial1'])
			worksheet.write(x,5,line.vacation_balance if line.vacation_balance else 0, formats['numberdos'])
			worksheet.write(x,6,line.expended_days if line.expended_days else 0, formats['numberdos'])
			worksheet.write(x,7,line.total if line.total else 0, formats['numberdos'])
			x += 1

		widths = [5,10,38,13,13,13,11,11]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(route + 'control_vacaciones.xlsx', 'rb')
		return self.env['popup.it'].get_file('control_vacaciones.xlsx', base64.encodestring(b''.join(f.readlines())))

class HrVacationControlLine(models.Model):
	_name = 'hr.vacation.control.line'
	_description = 'Vacation Control Line'

	vacation_control_id = fields.Many2one('hr.vacation.control', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Apellidos y Nombres')
	identification_id = fields.Char(related='employee_id.identification_id', string='DNI')
	payroll_period = fields.Many2one('hr.payslip.run', string='Periodo Planilla')
	accrued_period = fields.Many2one('hr.payslip.run', string='Periodo Devengue')
	expended_days = fields.Integer(string='Dias Gozados')
	vacation_balance = fields.Integer(string='Saldo Vacaciones')
	total = fields.Integer(string='Total')
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año')