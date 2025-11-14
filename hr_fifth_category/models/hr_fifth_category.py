# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrFifthCategory(models.Model):
	_name = 'hr.fifth.category'
	_description = 'Fifth Category'

	name = fields.Char(compute='_get_name')
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.fifth.category.line', 'fifth_category_id', states={'exported': [('readonly', True)]})
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

	@api.depends('payslip_run_id')
	def _get_name(self):
		for record in self:
			if record.payslip_run_id:
				record.name = 'Quinta {0}'.format(record.payslip_run_id.name)

	def turn_draft(self):
		self.state = 'draft'

	def export_fifth(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		for line in self.line_ids:
			fifth_inp = line.slip_id.input_line_ids.filtered(lambda inp: inp.input_type_id == MainParameter.fifth_category_input_id)
			fifth_inp.amount = line.monthly_ret
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def generate_fifth(self):
		self.line_ids.unlink()
		for slip in self.payslip_run_id.slip_ids:
			self.env['hr.fifth.category.line'].create({
													'fifth_category_id': self.id,
													'slip_id': slip.id,
													'static': True
												})
		self.line_ids.compute_fifth_line()
		return self.env['popup.it'].get_message('Se genero la Quinta de manera Correcta')
	
	def recompute_fifth(self):
		self.line_ids.compute_fifth_line()

	def get_excel_fifth(self):
		import io
		from xlsxwriter.workbook import Workbook
		Employee = self.env['hr.employee']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Quinta.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('QUINTA %s' % self.payslip_run_id.name)
		worksheet.set_tab_color('blue')
		HEADERS = ['EMPLEADO', 'REMUNERACION MENSUAL', 'REM. PROY. SEGUN CONTRATO', 'REMUNERACION PROYECTADA', 'GRATIFICACION JULIO', 'GRATIFICACION DICIEMBRE',
				'REM. PROY. OTROS EMPLEADORES', 'REMUNERACIONES ANTERIORES', 'TOTAL PROYECTADO', 'DEDUCCION 7UIT', 'RENTA NETA', 'IMPUESTO PROYECTADO',
				'RETENCION MESES ANTERIORES', 'RETENCION OTROS EMPLEADORES', 'RETENCION ANUAL', 'RENTA MENSUAL', 'REMUNERACION EXTRAORDINARIA', 'TOTAL RENTA NETA',
				'RETENCION EXTRAORDINARIA', 'RETENCION MENSUAL']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x = 1
		for line in self.line_ids:
			worksheet.write(x, 0, line.employee_id.name, formats['especial1'])
			worksheet.write(x, 1, line.monthly_rem, formats['numberdos'])
			worksheet.write(x, 2, line.contrac_proy_rem, formats['numberdos'])
			worksheet.write(x, 3, line.proy_rem, formats['numberdos'])
			worksheet.write(x, 4, line.grat_july, formats['numberdos'])
			worksheet.write(x, 5, line.grat_december, formats['numberdos'])
			worksheet.write(x, 6, line.other_emp_proy_rem, formats['numberdos'])
			worksheet.write(x, 7, line.past_rem, formats['numberdos'])
			worksheet.write(x, 8, line.total_proy, formats['numberdos'])
			worksheet.write(x, 9, line.seven_uit, formats['numberdos'])
			worksheet.write(x, 10, line.net_rent, formats['numberdos'])
			worksheet.write(x, 11, line.tax_proy, formats['numberdos'])
			worksheet.write(x, 12, line.past_months_ret, formats['numberdos'])
			worksheet.write(x, 13, line.other_emp_ret, formats['numberdos'])
			worksheet.write(x, 14, line.annual_ret, formats['numberdos'])
			worksheet.write(x, 15, line.monthly_rent, formats['numberdos'])
			worksheet.write(x, 16, line.ext_rem, formats['numberdos'])
			worksheet.write(x, 17, line.total_net_rent, formats['numberdos'])
			worksheet.write(x, 18, line.ext_ret, formats['numberdos'])
			worksheet.write(x, 19, line.monthly_ret, formats['numberdos'])
			x += 1
		widths = [40] + 19 * [20]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		workbook.close()

		f = open(route + 'Quinta.xlsx', 'rb')
		return self.env['popup.it'].get_file('Quinta %s.xlsx' % self.payslip_run_id.name, base64.encodestring(b''.join(f.readlines())))

class HrFifthCategoryLine(models.Model):
	_name = 'hr.fifth.category.line'
	_description = 'Fifth Category Line'

	fifth_category_id = fields.Many2one('hr.fifth.category', ondelete='cascade')
	slip_id = fields.Many2one('hr.payslip', string='Mes', required=True)
	employee_id = fields.Many2one(related='slip_id.employee_id', string='Empleado', required=True)
	monthly_rem = fields.Float(string='Remuneracion Mensual')
	contrac_proy_rem = fields.Float(string='Rem. Proy. Segun Contrato', help='Remuneracion Proyectada Segun Contrato')
	proy_rem = fields.Float(string='Remuneracion Proyectada')
	grat_july = fields.Float(string='Gratificacion Julio')
	grat_december = fields.Float(string='Gratificacion Diciembre')
	other_emp_proy_rem = fields.Float(string='Rem. Proy. Otros Empleadores')
	past_rem = fields.Float(string='Remuneraciones Anteriores')
	total_proy = fields.Float(string='Total Proyectado')
	seven_uit = fields.Float(string='Deduccion 7 UIT')
	net_rent = fields.Float(string='Renta Neta')
	tax_proy = fields.Float(string='Impuesto Proyectado')
	past_months_ret = fields.Float(string='Retencion Meses Anteriores')
	other_emp_ret = fields.Float(string='Retencion Otros Empleadores')
	annual_ret = fields.Float(string='Retencion Anual')
	monthly_rent = fields.Float(string='Renta Mensual')
	ext_rem = fields.Float(string='Remuneracion Extraordinaria')
	total_net_rent = fields.Float(string='Total Renta Neta')
	ext_ret = fields.Float(string='Retencion Extraordinaria')
	monthly_ret = fields.Float(string='Retencion Mensual')
	real_other_emp_rem = fields.Float(string='Rem. Real Otros Empleadores')
	static = fields.Boolean(help='This is just a helper field to know where the field was created', default=False)

	def get_past_rem(self, slip, date_from):
		past_lines = self.env['hr.fifth.category.line'].search([
														('slip_id.date_from', '>=', date_from),
														('slip_id.date_from', '<', slip.date_from),
														('employee_id', '=', slip.employee_id.id)
													])
		return sum(past_lines.mapped('monthly_rem')) + sum(past_lines.mapped('ext_rem'))

	def get_tax_proy(self, net_rent, lines):
		tax_proy = tax = 0
		for line in lines:
			if net_rent > line.limit and line.limit > 0:
				tax_proy += (line.limit - tax) * line.rate * 0.01
				tax += line.limit - tax
			else:
				tax_proy += (net_rent - tax) * line.rate * 0.01
				break
		return tax_proy

	def get_past_months_ret(self, slip, date_from):
		if slip.date_from.month in (1,2,3):
			return 0
		if slip.date_from.month in (4, 5, 8, 9, 12):
			past_lines = self.env['hr.fifth.category.line'].search([
															('slip_id.date_from', '>=', date_from),
															('slip_id.date_from', '<', slip.date_from),
															('employee_id', '=', slip.employee_id.id)
														])
		if slip.date_from.month in (6, 7):
			past_lines = self.env['hr.fifth.category.line'].search([
															('slip_id.date_from', '>=', date_from),
															('slip_id.date_from', '<', date(date_from.year, 4, 30)),
															('employee_id', '=', slip.employee_id.id)
														])
		if slip.date_from.month in (10, 11):
			past_lines = self.env['hr.fifth.category.line'].search([
															('slip_id.date_from', '>=', date_from),
															('slip_id.date_from', '<', date(date_from.year, 8, 31)),
															('employee_id', '=', slip.employee_id.id)
														])

		return sum(past_lines.mapped('monthly_ret'))

	def get_month_equivalence_proy(self, month):
		return 12 - month

	def get_month_equivalence_rent(self, month):
		month_equivalence = [12, 12, 12, 9, 8, 8, 8, 5, 4, 4, 4, 1]
		return month_equivalence[month - 1]

	def compute_fifth_line(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		#This line was added because the user used to discard a line after the computation so this create 
		#a line whithout header and that cause compute errors
		self.env['hr.fifth.category.line'].search([('fifth_category_id', '=', None), ('id', 'not in', self.ids)]).unlink()

		for record in self:
			Slip = record.slip_id
			month = Slip.date_from.month
			proy_month = self.get_month_equivalence_proy(month)
			rent_month = self.get_month_equivalence_rent(month)
			FiscalYear = self.env['account.fiscal.year'].search([('date_from', '<=', Slip.date_from), ('date_to', '>=', Slip.date_from)])
			uit = FiscalYear.uit
			Employee, Contract = Slip.employee_id, Slip.contract_id
			if month == 7:
				grat_july = self.env['hr.gratification.line'].search([
																('gratification_id.type', '=', '07'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])
			if month == 12:
				grat_december = self.env['hr.gratification.line'].search([
																('gratification_id.type', '=', '12'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])
			record.monthly_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_afect_sr_id).total
			record.contrac_proy_rem = Contract.fifth_rem_proyected
			record.proy_rem = record.contrac_proy_rem * proy_month + record.monthly_rem
			record.grat_july = grat_july.total_grat if month == 7 and grat_july else Contract.grat_july_proyected
			record.grat_december = grat_december.total_grat if month == 12 and grat_december else Contract.grat_december_proyected
			record.past_rem = self.get_past_rem(Slip, FiscalYear.date_from)
			record.total_proy = record.proy_rem + record.grat_july + record.grat_december + record.other_emp_proy_rem + record.past_rem
			record.seven_uit = 7 * uit
			record.net_rent = record.total_proy - record.seven_uit
			tax_proy = self.get_tax_proy(record.net_rent, MainParameter.rate_limit_ids)
			record.tax_proy = 0 if tax_proy < 0 else tax_proy
			record.past_months_ret = self.get_past_months_ret(Slip, FiscalYear.date_from)
			record.annual_ret = record.tax_proy - record.past_months_ret - record.other_emp_ret
			record.monthly_rent = ReportBase.custom_round(record.annual_ret/rent_month, 2)
			record.ext_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_extr_sr_id).total
			record.total_net_rent = record.ext_rem + record.net_rent
			ext_ret = self.get_tax_proy(record.total_net_rent, MainParameter.rate_limit_ids) - record.tax_proy
			record.ext_ret = 0 if ext_ret < 0 else ext_ret
			record.monthly_ret = record.monthly_rent + record.ext_ret
			if not record.monthly_ret > 0 and not self._context.get('line_form', False):
				record.unlink()
