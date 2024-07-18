# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrGratification(models.Model):
	_name = 'hr.gratification'
	_description = 'Gratification'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True, states={'exported': [('readonly', True)]})
	fiscal_year_id = fields.Many2one('account.fiscal.year', string='Año Fiscal', required=True, states={'exported': [('readonly', True)]})
	with_bonus = fields.Boolean(string='Bonificacion 9%', default=False, states={'exported': [('readonly', True)]})
	months_and_days = fields.Boolean(string='Calcular Meses y Dias', default=False, states={'exported': [('readonly', True)]})
	type = fields.Selection([('07', 'Gratificacion Fiestas Patrias'),
							 ('12', 'Gratificacion Navidad')], string='Tipo Gratificacion', required=True, states={'exported': [('readonly', True)]})
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Periodo', required=True, states={'exported': [('readonly', True)]})
	deposit_date = fields.Date(string='Fecha de Deposito', required=True, states={'exported': [('readonly', True)]})
	line_ids = fields.One2many('hr.gratification.line', 'gratification_id', states={'exported': [('readonly', True)]})
	state = fields.Selection([('draft', 'Borrador'), ('exported', 'Exportado')], default='draft', string='Estado')

	@api.onchange('fiscal_year_id', 'type')
	def _get_period(self):
		for record in self:
			if record.type and record.fiscal_year_id.name:
				record.name = dict(self._fields['type'].selection).get(record.type) + ' ' + record.fiscal_year_id.name
				date_start = date(int(record.fiscal_year_id.name), int(record.type), 1)
				date_end = date(int(record.fiscal_year_id.name), int(record.type), 31)
				Period = self.env['hr.payslip.run'].search([('date_start', '=', date_start),
															('date_end', '=', date_end)], limit=1)
				if Period:
					record.payslip_run_id = Period.id

	def turn_draft(self):
		self.state = 'draft'

	def set_amounts(self, line_ids, Lot, MainParameter):
		inp_grat = MainParameter.gratification_input_id
		inp_bonus = MainParameter.bonus_nine_input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			grat_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_grat)
			bonus_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_bonus)
			grat_line.amount = line.total_grat
			bonus_line.amount = line.bonus_essalud

	def export_gratification(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_gratification_values()
		Lot = self.payslip_run_id
		self.set_amounts(self.line_ids, Lot, MainParameter)
		self.state = 'exported'
		return self.env['popup.it'].get_message('Se exporto exitosamente')

	def get_gratification(self):
		self.line_ids.unlink()
		self.env['hr.main.parameter'].compute_benefits(self, self.type)
		return self.env['popup.it'].get_message('Se calculo exitosamente')

	def get_excel_gratification(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file
		type = dict(self._fields['type'].selection).get(self.type)

		if not route:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%s %s.xlsx' % (type, self.fiscal_year_id.name)
		workbook = Workbook(route + doc_name)
		
		self.get_gratification_sheet(workbook, self.line_ids)

		workbook.close()
		f = open(route + doc_name, 'rb')
		return self.env['popup.it'].get_file(doc_name, base64.encodestring(b''.join(f.readlines())))

	def get_gratification_sheet(self, workbook, lines, liquidation=False):
		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)
		labor_regime = dict(self.env['hr.contract']._fields['labor_regime'].selection)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet('GRATIFICACION')
		worksheet.set_tab_color('blue')

		#### I'm separating this array of headers 'cause i need a dynamic limiter to set the totals at the end of the printing, i will use the HEADER variable to get the lenght and this will be my limiter'
		HEADERS = ['NRO. DOCUMENTO', 'APELLIDO MATERNO', 'APELLIDO PATERNO', 'NOMBRES', 'FECHA INGRESO', 'REGIMEN LABORAL','DISTRIBUCION ANALITICA', 'SEGURO', 'MES', 'DIAS']
		if liquidation:
			HEADERS = HEADERS[:5] + ['FECHA DE COMPUTO', 'FECHA DE CESE'] + HEADERS[5:]
		HEADERS_WITH_TOTAL = ['FALTAS', 'SUELDO', 'ASIGNACION FAMILIAR', 'COMISION', 'BONIFICACION', 'PROMEDIO HRS EXTRAS', 'REMUNERACION COMPUTABLE',
							  'MONTO POR MES', 'MONTO POR DIA', 'TOTAL FALTAS S/.', 'GRAT. POR MESES', 'GRAT. POR DIAS', 'TOTAL GRAT.', 'BONIFICACION 9%', 'TOTAL A PAGAR']
		
		worksheet = ReportBase.get_headers(worksheet, HEADERS + HEADERS_WITH_TOTAL, 0, 0, formats['boldbord'])
		x, y = 1, 0
		totals = [0] * len(HEADERS_WITH_TOTAL)
		limiter = len(HEADERS)

		for line in lines:

			worksheet.write(x, 0, line.identification_id or '', formats['especial1'])
			worksheet.write(x, 1, line.last_name or '', formats['especial1'])
			worksheet.write(x, 2, line.m_last_name or '', formats['especial1'])
			worksheet.write(x, 3, line.names or '', formats['especial1'])
			worksheet.write(x, 4, line.admission_date or '', formats['reverse_dateformat'])
			if liquidation:
				worksheet.write(x, 5, line.compute_date or '', formats['reverse_dateformat'])
				worksheet.write(x, 6, line.cessation_date or '', formats['reverse_dateformat'])
				y = 2
			worksheet.write(x, 5 + y, labor_regime.get(line.labor_regime) or '', formats['especial1'])
			worksheet.write(x, 6 + y, line.distribution_id or '', formats['especial1'])
			worksheet.write(x, 7 + y, line.social_insurance_id.name or '', formats['especial1'])
			worksheet.write(x, 8 + y, line.months or 0, formats['number'])
			worksheet.write(x, 9 + y, line.days or 0, formats['number'])
			worksheet.write(x, 10 + y, line.lacks or 0, formats['number'])
			worksheet.write(x, 11 + y, line.wage or 0, formats['numberdos'])
			worksheet.write(x, 12 + y, line.household_allowance or 0, formats['numberdos'])
			worksheet.write(x, 13 + y, line.commission or 0, formats['numberdos'])
			worksheet.write(x, 14 + y, line.bonus or 0, formats['numberdos'])
			worksheet.write(x, 15 + y, line.extra_hours or 0, formats['numberdos'])
			worksheet.write(x, 16 + y, line.computable_remuneration or 0, formats['numberdos'])
			worksheet.write(x, 17 + y, line.amount_per_month or 0, formats['numberdos'])
			worksheet.write(x, 18 + y, line.amount_per_day or 0, formats['numberdos'])
			worksheet.write(x, 19 + y, line.amount_per_lack or 0, formats['numberdos'])
			worksheet.write(x, 20 + y, line.grat_per_month or 0, formats['numberdos'])
			worksheet.write(x, 21 + y, line.grat_per_day or 0, formats['numberdos'])
			worksheet.write(x, 22 + y, line.total_grat or 0, formats['numberdos'])
			worksheet.write(x, 23 + y, line.bonus_essalud or 0, formats['numberdos'])
			worksheet.write(x, 24 + y, line.total or 0, formats['numberdos'])
			
			totals[0] += line.lacks
			totals[1] += line.wage
			totals[2] += line.household_allowance
			totals[3] += line.commission
			totals[4] += line.bonus
			totals[5] += line.extra_hours
			totals[6] += line.computable_remuneration
			totals[7] += line.amount_per_month
			totals[8] += line.amount_per_day
			totals[9] += line.amount_per_lack
			totals[10] += line.grat_per_month
			totals[11] += line.grat_per_day
			totals[12] += line.total_grat
			totals[13] += line.bonus_essalud
			totals[14] += line.total

			x += 1
		x += 1
		for total in totals:
			worksheet.write(x, limiter, total, formats['numbertotal'])
			limiter += 1

		widths = [14, 12, 12, 10, 10, 10, 8, 5, 5, 8, 8, 13, 11, 16, 13, 16, 9, 9, 12, 11, 11, 8, 19, 10]
		if liquidation:
			widths = widths[:5] + [10, 10] + widths[5:]
		worksheet = ReportBase.resize_cells(worksheet, widths)

class HrGratificationLine(models.Model):
	_name = 'hr.gratification.line'
	_description = 'Gratification Line'

	liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
	gratification_id = fields.Many2one('hr.gratification', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee')
	contract_id = fields.Many2one('hr.contract')
	identification_id = fields.Char(related='employee_id.identification_id', string='Nro Documento')
	last_name = fields.Char(related='employee_id.last_name', string='Apellido Paterno')
	m_last_name = fields.Char(related='employee_id.m_last_name', string='Apellido Materno')
	names = fields.Char(related='employee_id.names', string='Nombres')
	admission_date = fields.Date(string='Fecha de Ingreso')
	compute_date = fields.Date(string='Fecha de Computo')
	cessation_date = fields.Date(string='Fecha de Cese')
	labor_regime = fields.Selection(related='contract_id.labor_regime', string='Regimen Laboral')
	social_insurance_id = fields.Many2one(related='contract_id.social_insurance_id', string='Seguro Social')
	distribution_id = fields.Char(string='Distribucion Analitica')
	months = fields.Integer(string='Meses')
	days = fields.Integer(string='Dias')
	lacks = fields.Integer(string='Faltas')
	wage = fields.Float(string='Sueldo')
	household_allowance = fields.Float(string='Asignacion Familiar')
	commission = fields.Float(string='Comision')
	bonus = fields.Float(string='Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extra')
	computable_remuneration = fields.Float(string='Remuneracion Computable')
	amount_per_month = fields.Float(string='Monto por Mes')
	amount_per_day = fields.Float(string='Monto por Dia')
	amount_per_lack = fields.Float(string='Total Faltas S/.')
	grat_per_month = fields.Float(string='Grat. por Meses')
	grat_per_day = fields.Float(string='Grat. por Dias')
	total_grat = fields.Float(string='Total Grat.')
	bonus_essalud = fields.Float(string='Bonif. 9%')
	total = fields.Float(string='Total a Pagar')