# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from datetime import *
from math import modf

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	slip_ids = fields.One2many(states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

	def action_open_payslips(self):
		rec = super(HrPayslipRun, self).action_open_payslips()
		rec['context'] = {'default_payslip_run_id': self.id}
		return rec

	def set_draft(self):
		self.slip_ids.action_payslip_cancel()
		self.slip_ids.unlink()
		self.state = 'draft'

	def compute_wds_by_lot(self):
		self.slip_ids.compute_wds()

	def recompute_payslips(self):
		self.slip_ids.generate_inputs_and_wd_lines(True)
		self.slip_ids.compute_sheet()

	def close_payroll(self):
		self.state = 'close'

	def reopen_payroll(self):
		self.state = 'verify'

	def _get_tab_payroll_sql(self):
		struct_id = self.slip_ids[0].struct_id.id
		sql = """
			select
			he.id as employee_id,
			he.identification_id,
			hc.date_start,
			hm.name as membership,
			had.name as distribution,
			hsr.code,
			sum(hpl.total)
			from hr_payslip hp
			inner join hr_payslip_line hpl on hpl.slip_id = hp.id
			inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
			inner join hr_employee he on he.id = hp.employee_id
			inner join hr_contract hc on hc.id = hp.contract_id
			left join hr_membership hm on hm.id = hc.membership_id
			left join hr_analytic_distribution had on had.id = hc.distribution_id
			where hp.id in ({ids})
			and hsr.appears_on_payslip = true
			and hsr.active = true
			and hsr.company_id = {company}
			and hsr.struct_id = {struct_id}
			group by he.identification_id, he.id, hc.date_start, hsr.code, hm.name, had.name, hsr.sequence
			order by he.identification_id, hsr.sequence
		""".format(
				ids = ','.join(list(map(str, self.slip_ids.ids))),
				company = self.company_id.id,
				struct_id = struct_id
			)
		return sql

	def tab_payroll(self):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file

		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'Planilla_Tabular.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Planilla Tabular")
		worksheet.set_tab_color('blue')
		self._cr.execute(self._get_tab_payroll_sql())
		data = self._cr.dictfetchall()
		print(data)
		x, y = 0, 6
		limit = len(data[0] if data else 0)
		struct_id = self.slip_ids[0].struct_id.id
		SalaryRules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True), ('struct_id', '=', struct_id)], order='sequence')
		names = SalaryRules.mapped('name')
		codes = SalaryRules.mapped('code')
		size = len(codes)
		
		worksheet.write(x, 0, 'NRO IDENTIFICACION', formats['boldbord'])
		worksheet.write(x, 1, 'NOMBRE', formats['boldbord'])
		worksheet.write(x, 2, 'TITULO DE TRABAJO', formats['boldbord'])
		worksheet.write(x, 3, 'INICIO DE CONTRATO', formats['boldbord'])
		worksheet.write(x, 4, 'AFILIACION', formats['boldbord'])
		worksheet.write(x, 5, 'DISTRIBUCION ANALITICA', formats['boldbord'])
		
		for name in names:
			worksheet.write(x, y, name, formats['boldbord'])
			y += 1
		x += 1
		table = []
		row = []
		aux_id, limit = '', len(data)
		for c, line in enumerate(data, 1):
			if aux_id != line['employee_id']:
				if len(row) > 0:
					table.append(row)
					x += 1
				row = []
				employee = self.env['hr.employee'].browse(line['employee_id'])
				worksheet.write(x, 0, line['identification_id'] if line['identification_id'] else '', formats['especial1'])
				worksheet.write(x, 1, employee.name if employee.name else '', formats['especial1'])
				worksheet.write(x, 2, employee.job_title if employee.job_title else '', formats['especial1'])
				worksheet.write(x, 3, line['date_start'] if line['date_start'] else '', formats['dateformat'])
				worksheet.write(x, 4, line['membership'] if line['membership'] else '', formats['especial1'])
				worksheet.write(x, 5, line['distribution'] if line['distribution'] else '', formats['especial1'])
				worksheet.write(x, 6, line['sum'] if line['sum'] else 0.0, formats['numberdos'])
				row.append(line['sum'])
				y = 6
				aux_id = line['employee_id']
			else:
				y += 1
				worksheet.write(x, y, line['sum'] if line['sum'] else 0.0, formats['numberdos'])
				aux_id = line['employee_id']
				row.append(line['sum'])
				if c == limit:
					table.append(row)
					x += 1

		zipped_table = zip(*table)
		y = 6
		for row in zipped_table:
			worksheet.write(x, y, sum(list(row)), formats['numbertotal'])
			y += 1
		widths = [18, 40, 22, 12, 16] + size * [19]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'Planilla_Tabular.xlsx', 'rb')
		return self.env['popup.it'].get_file('Planilla %s.xlsx' % self.name, base64.encodestring(b''.join(f.readlines())))

	def afp_net(self):
		import io
		from xlsxwriter.workbook import Workbook
		if len(self.ids) > 1:
			raise UserError('No se puede seleccionar mas de un registro para este proceso')
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		directory = MainParameter.dir_create_file
		insurable_remuneration = MainParameter.insurable_remuneration
		if not directory:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		workbook = Workbook(directory + 'AFP_NET.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("AFP NET")
		worksheet.set_tab_color('blue')
		x = 0
		for c, slip in enumerate(self.slip_ids):
			if slip.contract_id.membership_id.is_afp:
				Contract = slip.contract_id
				Employee = slip.contract_id.employee_id
				FirstContract = self.env['hr.contract'].get_first_contract(Employee, Contract)
				ir_line = self.env['hr.payslip.line'].search([('salary_rule_id', '=', insurable_remuneration.id),('slip_id', '=', slip.id)])
				worksheet.write(x, 0, c)
				worksheet.write(x, 1, Contract.cuspp if Contract.cuspp else '')
				worksheet.write(x, 2, Employee.type_document_id.afp_code if Employee.type_document_id.afp_code else '')
				worksheet.write(x, 3, Employee.identification_id if Employee.identification_id else '')
				worksheet.write(x, 4, Employee.last_name if Employee.last_name else '')
				worksheet.write(x, 5, Employee.m_last_name if Employee.m_last_name else '')
				worksheet.write(x, 6, Employee.names if Employee.names else '')
				worksheet.write(x, 7, 'N' if Contract.situation_id.code == '0' else 'S')
				worksheet.write(x, 8, 'S' if FirstContract.date_start >= self.date_start and FirstContract.date_start <= self.date_end else 'N')
				worksheet.write(x, 9, 'S' if FirstContract.date_end and FirstContract.date_end >= self.date_start and FirstContract.date_end <= self.date_end else 'N')
				worksheet.write(x, 10, Contract.exception if Contract.exception else '')
				worksheet.write(x, 11, ir_line.total if ir_line.total else 0.00, formats['numberdosespecial'])
				worksheet.write(x, 12, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 13, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 14, 0.00, formats['numberdosespecial'])
				worksheet.write(x, 15, Contract.work_type if Contract.work_type else 'N')
				x += 1

		widths = [2, 15, 2, 12, 20, 20, 20, 2, 2, 2, 2, 8, 8, 8, 8, 2]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(directory + 'AFP_NET.xlsx', 'rb')
		return self.env['popup.it'].get_file('AFP_NET.xlsx',base64.encodestring(b''.join(f.readlines())))

	def export_plame(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.rem' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select
						min(htd.sunat_code) as doc_type,
						he.identification_id as dni,
						sr.sunat_code as sunat,
						sum(hpl.total) as amount_earn,
						sum(hpl.total) as amount_paid
						from hr_payslip_run hpr
						inner join hr_payslip hp on hpr.id = hp.payslip_run_id
						inner join hr_payslip_line hpl on hp.id = hpl.slip_id
						inner join (select * from hr_salary_rule where company_id= %d) as sr on sr.code = hpl.code
						inner join hr_employee he on he.id = hpl.employee_id
						inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where  hpr.id = %d
						and he.id = %d
						and sr.sunat_code != ''
						group by sr.sunat_code, he.identification_id
						order by sr.sunat_code
						""" % (self.env.company.id,payslip_run.id, payslip.employee_id.id)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						f.write("%s|%s|%s|%s|%s|\r\n" % (
									line['doc_type'],
									line['dni'],
									line['sunat'],
									line['amount_earn'],
									line['amount_paid']
								))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.rem' % (first, second, self.company_id.vat),base64.encodestring(b''.join(f.readlines())))

	def export_plame_hours(self):
		if len(self.ids) > 1:
			raise UserError('Solo se puede mostrar una planilla a la vez, seleccione solo una nomina')
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')

		first = datetime.strftime(self.date_end, '%Y-%m-%d')[:4]
		second = datetime.strftime(self.date_end, '%Y-%m-%d')[5:7]
		doc_name = '%s0601%s%s%s.jor' % (MainParameter.dir_create_file, first, second, self.company_id.vat)

		f = open(doc_name, 'w+')
		for payslip_run in self.browse(self.ids):
			employees = []
			for payslip in payslip_run.slip_ids:
				if payslip.employee_id.id not in employees:
					sql = """
						select
						min(htd.sunat_code) as doc_type,
						he.identification_id as dni,
						sum(case when hpwd.wd_type_id in ({fal}) then hpwd.number_of_days else 0 end) as fal,
						sum(case when hpwd.wd_type_id in ({hext}) then hpwd.number_of_hours else 0 end) as hext,
						sum(case when hpwd.wd_type_id in ({dvac}) then hpwd.number_of_days else 0 end) as dvac,
						min(rc.hours_per_day) as hours_per_day
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join resource_calendar rc on rc.id = hc.resource_calendar_id
						inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
						inner join hr_payslip_worked_days_type hpwdt on hpwdt.id = hpwd.wd_type_id
						left join hr_type_document htd on htd.id = he.type_document_id
						where hp.payslip_run_id = {pr_id}
						and hp.employee_id = {emp_id}
						and hpwd.wd_type_id in ({fal},{hext},{dvac})
						group by htd.sunat_code, he.identification_id
						""".format(
								pr_id = payslip_run.id,
								emp_id = payslip.employee_id.id,
								fal = ','.join(str(id) for id in MainParameter.wd_dnlab.ids),
								hext = ','.join(str(id) for id in MainParameter.wd_ext.ids),
								dvac = ','.join(str(id) for id in MainParameter.wd_dvac.ids)
								)
					self._cr.execute(sql)
					data = self._cr.dictfetchall()
					for line in data:
						dlab = payslip.get_dlabs()
						hlab = modf(dlab * line['hours_per_day'])
						f.write("%s|%s|%d|0|%d|0|\r\n" % (
									line['doc_type'],
									line['dni'],
									hlab[1],
									line['hext']
								))
				employees.append(payslip.employee_id.id)
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('0601%s%s%s.jor' % (first, second, self.company_id.vat),base64.encodestring(b''.join(f.readlines())))