# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
import base64

class HrVacationRole(models.Model):
	_name = 'hr.vacation.role'
	_description = 'Vacation Role'

	name = fields.Char()
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True)
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Mes', required=True)
	line_ids = fields.One2many('hr.vacation.role.line', 'role_id')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)

	@api.onchange('fiscal_year_id', 'payslip_run_id')
	def _get_name(self):
		for record in self:
			if record.fiscal_year_id and record.payslip_run_id:
				month = self.env['hr.main.parameter'].get_month_name(record.payslip_run_id.date_start.month)
				record.name = '%s %s' % (month, record.fiscal_year_id.name)

	def get_vacation_role(self):
		self.line_ids.unlink()
		Lot = self.payslip_run_id
		for Slip in Lot.slip_ids:
			if Slip.contract_id.situation_id.code == '0':
				continue
			else:
				Contract = self.env['hr.contract'].get_first_contract(Slip.employee_id, Slip.contract_id)
				if Contract.date_start.month == Lot.date_start.month and Contract.date_start.year < int(self.fiscal_year_id.name):
					self.env['hr.vacation.role.line'].create({
							'role_id': self.id,
							'employee_id': Slip.employee_id.id,
							'vacation_date': date(int(self.fiscal_year_id.name), Contract.date_start.month, Contract.date_start.day)
						})
		return self.env['popup.it'].get_message('Se calculo el rol exitosamente')

	def get_excel_vacation_role(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Rol_Vacaciones.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ASISTENCIAS############
		worksheet = workbook.add_worksheet(self.name)
		worksheet.set_tab_color('blue')
		HEADERS = ['NRO. IDENTIFICACION', 'EMPLEADO', 'FECHA DE VACACIONES']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x = 1
		for line in self.line_ids:
			worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
			worksheet.write(x, 1, line.employee_id.name or '', formats['especial1'])
			worksheet.write(x, 2, line.vacation_date or '', formats['reverse_dateformat'])
			x += 1

		widths = [18, 30, 16]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'Rol_Vacaciones.xlsx', 'rb')
		return self.env['popup.it'].get_file('Rol Vacaciones %s.xlsx' % self.name, base64.encodestring(b''.join(f.readlines())))

class HrVacationRoleLine(models.Model):
	_name = 'hr.vacation.role.line'
	_description = 'Vacation Role Line'

	role_id = fields.Many2one('hr.vacation.role', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro. Identificacion')
	vacation_date = fields.Date(string='Fecha de Vacaciones')