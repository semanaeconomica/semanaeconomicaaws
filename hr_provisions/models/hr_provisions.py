# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from decimal import *
from datetime import *
import base64
from collections import Counter
from odoo.tools import date_utils


class HrProvisiones(models.Model):
	_name = 'hr.provisiones'
	_description = 'Provisiones'

	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	payslip_run_id = fields.Many2one('hr.payslip.run','Periodo')
	gratificacion_id = fields.Many2one('hr.gratification','Gratificacion')
	asiento_contable = fields.Many2one('account.move','Asiento Contable')
	cts_debe = fields.Many2one('account.account')
	cts_haber = fields.Many2one('account.account')
	grati_debe = fields.Many2one('account.account')
	grati_haber = fields.Many2one('account.account')
	boni_debe = fields.Many2one('account.account')
	boni_haber = fields.Many2one('account.account')
	vaca_debe = fields.Many2one('account.account')
	vaca_haber = fields.Many2one('account.account')
	cts_lines = fields.One2many('hr.provisiones.cts.line','provision_id')
	grati_lines = fields.One2many('hr.provisiones.grati.line','provision_id')
	vaca_lines = fields.One2many('hr.provisiones.vaca.line','provision_id')

	def actualizar(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if self.cts_lines:
			self.env['hr.provisiones.cts.line'].search([('provision_id','=',self.id)]).unlink()
		if self.grati_lines:
			self.env['hr.provisiones.grati.line'].search([('provision_id','=',self.id)]).unlink()
		if self.vaca_lines:
			self.env['hr.provisiones.vaca.line'].search([('provision_id','=',self.id)]).unlink()

		employees = self.env['hr.employee'].search([])
		grati = self.env['hr.gratification'].browse(self.gratificacion_id.id)
		date_start = date_utils.subtract(self.payslip_run_id.date_start, months=6)
		date_end = date_utils.subtract(self.payslip_run_id.date_start, days=1)
		comi_ids=[]
		boni_ids=[]
		extrhors_ids=MainParameter.extra_hours_sr_id.id
		
		for o in MainParameter.commission_sr_ids:
			comi_ids.append(o.id)
		

		for o in MainParameter.bonus_sr_ids:
			boni_ids.append(o.id)


		for employee in employees:
			sql = """
				select 
				max(hc.id) as contract_id,
				max(hc.date_start) as date_start,
				sum(hpl.total) as total,
				max(hsi.percent) as porcentaje
				from hr_payslip hp
				inner join hr_payslip_line hpl on hpl.slip_id = hp.id
				inner join hr_contract hc on hc.id = hp.contract_id
				left join hr_social_insurance hsi on hsi.id = hc.social_insurance_id
				where hp.employee_id = %d
				and hp.date_from = '%s'
				and hp.date_to = '%s'
				and hc.labor_regime in ('general','small')
				and hpl.code = '%s'
				group by hp.employee_id
			"""%(employee.id, self.payslip_run_id.date_start, self.payslip_run_id.date_end, MainParameter.basic_sr_id.code)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()

			
			payslips = self.env['hr.payslip'].search([('employee_id','=',employee.id),
													  ('date_from','=',self.payslip_run_id.date_start),
													  ('date_to','=',self.payslip_run_id.date_end)])

			if payslips:

				
				payslips1 = self.env['hr.payslip'].search([('employee_id','=',employee.id),
													  ('date_from','>=',date_start),
													  ('date_to','<=',date_end)])

				ncomis=0
				nboni=0
				nextra =0
				amount_comisi=0
				amount_bonifi=0
				amount_hextra=0
				for l in payslips1:
					for k in l.line_ids:
						if k.salary_rule_id.id in comi_ids:
							amount_comisi=amount_comisi+k.total
							ncomis=ncomis+1

						if k.salary_rule_id.id in boni_ids:
							amount_bonifi=amount_bonifi+k.total
							nboni=nboni+1

						if k.salary_rule_id.id == extrhors_ids:
							amount_hextra=amount_hextra + k.total
							nextra=nextra+1

				for payslip in data:
					Contract = self.env['hr.contract'].browse(payslip['contract_id'])
					date_mo = date_utils.subtract(self.payslip_run_id.date_start, months=1)
					if ncomis<3:
						if Contract.date_start<=date_mo:
							amount_comisi=0

					if nboni<3:
						amount_bonifi=0

					if nextra<3:
						if Contract.date_start<=date_mo:
							amount_hextra=0

					line = grati.line_ids.filtered(lambda line: line.employee_id.id == employee.id)

					if not Contract.less_than_four:
						self.env['hr.provisiones.cts.line'].create({
								'provision_id':self.id,
								'nro_doc':employee.identification_id,
								'employee_id':employee.id,
								'contract_id':payslip['contract_id'],
								'fecha_ingreso':payslip['date_start'],
								'distribution_id':self.env['hr.contract'].browse(payslip['contract_id']).distribution_id.name,
								'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
								'asignacion':102.50 if employee.children > 0 else 0,
								'commission': ReportBase.custom_round(amount_comisi/6,2) if line else 0,
								'bonus': ReportBase.custom_round(amount_bonifi/6,2) if line else 0,
								'extra_hours': ReportBase.custom_round(amount_hextra/6,2) if line else 0,
								'un_sexto_grati': ReportBase.custom_round(line.total_grat/6,2) if line else 0
							})
						self.env['hr.provisiones.vaca.line'].create({
								'provision_id':self.id,
								'nro_doc':employee.identification_id,
								'employee_id':employee.id,
								'contract_id':payslip['contract_id'],
								'fecha_ingreso':payslip['date_start'],
								'distribution_id':self.env['hr.contract'].browse(payslip['contract_id']).distribution_id.name,
								'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
								'asignacion':102.50 if employee.children > 0 else 0,
								'commission': ReportBase.custom_round(amount_comisi/6,2) if line else 0,
								'bonus': ReportBase.custom_round(amount_bonifi/6,2) if line else 0,
								'extra_hours': ReportBase.custom_round(amount_hextra/6,2) if line else 0
							})
					self.env['hr.provisiones.grati.line'].create({
							'provision_id':self.id,
							'nro_doc':employee.identification_id,
							'employee_id':employee.id,
							'contract_id':payslip['contract_id'],
							'fecha_ingreso':payslip['date_start'],
							'distribution_id':self.env['hr.contract'].browse(payslip['contract_id']).distribution_id.name,
							'basico': self.env['hr.contract'].browse(payslip['contract_id']).wage,
							'asignacion':102.50 if employee.children > 0 else 0,
							'commission': ReportBase.custom_round(line.commission/6,2) if line else 0,
							'bonus': ReportBase.custom_round(line.bonus/6,2) if line else 0,
							'extra_hours': ReportBase.custom_round(line.extra_hours/6,2) if line else 0,
							'tasa':payslip['porcentaje']
						})
		return self.env['popup.it'].get_message('Se actualizo de manera correcta')

	#		Commissions = Bonus = ExtraHours = self.env['hr.payslip.line']
	# 		Commissions += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.commission_sr_ids and line.total > 0)
	# 		Bonus += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.bonus_sr_ids and line.total > 0)
	# 		ExtraHours += SalaryRules.filtered(lambda line: line.salary_rule_id == MainParameter.extra_hours_sr_id and line.total > 0)
	#
	# 		commission = self.calculate_bonus(admission_date, date_from, bonus_months, Commissions)
	# 		bonus = self.calculate_bonus(admission_date, date_from, bonus_months, Bonus)
	# 		extra_hours = self.calculate_bonus(admission_date, date_from, bonus_months, ExtraHours)
	# 		computable_remuneration = wage + household_allowance + commission + bonus + extra_hours

	# def calculate_bonus(self, admission_date, date_from, months, Lines):
	# 	ReportBase = self.env['report.base']
	# 	Codes = Counter(Lines.mapped('code'))
	# 	total = 0
	# 	for key, value in Codes.items():
	# 		if months >= 3 and value >= 3:
	# 			amount = sum(Lines.filtered(lambda line: line.code == key).mapped('total'))
	# 			if admission_date > date_from:
	# 				amount = ReportBase.custom_round(amount/months, 2)
	# 			else:
	# 				amount = ReportBase.custom_round(amount/6, 2)
	# 		else:
	# 			amount = 0
	# 		total += amount
	# 	return total


	def get_move_lines(self):
		ReportBase = self.env['report.base']
		montos = []
		for line in self.cts_lines:
			for cal in line.contract_id.distribution_id.line_ids:
				if not any(i.get('cuenta',None) == cal.analytic_id.id for i in montos):
					montos.append({'cuenta':cal.analytic_id.id,
								   'monto':ReportBase.custom_round(line.provisiones_cts * cal.percent/100, 2)})
				else:
					for i in montos:
						if i['cuenta'] == cal.analytic_id.id:
							i['monto'] = ReportBase.custom_round(i['monto'] + (line.provisiones_cts * cal.percent/100), 2)
		
		montos_grati = []
		for line in self.grati_lines:
			for cal in line.contract_id.distribution_id.line_ids:
				if not any(i.get('cuenta',None) == cal.analytic_id.id for i in montos_grati):
					montos_grati.append({'cuenta':cal.analytic_id.id,
										 'monto':ReportBase.custom_round(line.provisiones_grati * cal.percent/100, 2)})
				else:
					for i in montos_grati:
						if i['cuenta'] == cal.analytic_id.id:
							i['monto'] = ReportBase.custom_round(i['monto'] + (line.provisiones_grati * cal.percent/100), 2)

		montos_boni = []
		for line in self.grati_lines:
			for cal in line.contract_id.distribution_id.line_ids:
				if not any(i.get('cuenta',None) == cal.analytic_id.id for i in montos_boni):
					montos_boni.append({'cuenta':cal.analytic_id.id,
										'monto':ReportBase.custom_round(line.boni_grati * cal.percent/100, 2)})
				else:
					for i in montos_boni:
						if i['cuenta'] == cal.analytic_id.id:
							i['monto'] = ReportBase.custom_round(i['monto'] + (line.boni_grati * cal.percent/100), 2)

		montos_vaca = []
		for line in self.vaca_lines:
			for cal in line.contract_id.distribution_id.line_ids:
				if not any(i.get('cuenta',None) == cal.analytic_id.id for i in montos_vaca):
					montos_vaca.append({'cuenta':cal.analytic_id.id,
										'monto':ReportBase.custom_round(line.provisiones_vaca * cal.percent/100, 2)})
				else:
					for i in montos_vaca:
						if i['cuenta'] == cal.analytic_id.id:
							i['monto'] = ReportBase.custom_round(i['monto'] + (line.provisiones_vaca * cal.percent/100), 2)
		credit = 0
		move_lines = []
		for monto in montos:
			move_lines.append({
					'account_id':self.cts_debe.id,
					'analytic_account_id':monto['cuenta'],
					'debit':monto['monto'],
					'credit':0,
					'name':'Provision - ' + self.payslip_run_id.name
				})
			credit += monto['monto']
		
		credit_grati = 0
		for monto_grati in montos_grati:
			move_lines.append({
					'account_id':self.grati_debe.id,
					'analytic_account_id':monto_grati['cuenta'],
					'debit':monto_grati['monto'],
					'credit':0,
					'name':'Provision - ' + self.payslip_run_id.name
				})
			credit_grati += monto_grati['monto']

		credit_boni = 0
		for monto_boni in montos_boni:
			move_lines.append({
					'account_id':self.boni_debe.id,
					'analytic_account_id':monto_boni['cuenta'],
					'debit':monto_boni['monto'],
					'credit':0,
					'name':'Provision - ' + self.payslip_run_id.name
				})
			credit_boni += monto_boni['monto']

		credit_vaca = 0
		for monto_vaca in montos_vaca:
			move_lines.append({
					'account_id':self.vaca_debe.id,
					'analytic_account_id':monto_vaca['cuenta'],
					'debit':monto_vaca['monto'],
					'credit':0,
					'name':'Provision - ' + self.payslip_run_id.name
				})
			credit_vaca += monto_vaca['monto']
		
		c = 0
		for line in self.cts_lines:
			c += line.provisiones_cts
			move_lines.append({
					'account_id':self.cts_haber.id,
					'debit':0,
					'credit':line.provisiones_cts,
					'name':'Provision - ' + self.payslip_run_id.name,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else None
				})
		for line in self.grati_lines:
			c += line.provisiones_grati
			move_lines.append({
					'account_id':self.grati_haber.id,
					'debit':0,
					'credit':line.provisiones_grati,
					'name':'Provision - ' + self.payslip_run_id.name,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else None
				})
		for line in self.grati_lines:
			c += line.boni_grati
			move_lines.append({
					'account_id':self.boni_haber.id,
					'debit':0,
					'credit':line.boni_grati,
					'name':'Provision - ' + self.payslip_run_id.name,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else None
				})
		for line in self.vaca_lines:
			c += line.provisiones_vaca 
			move_lines.append({
					'account_id':self.vaca_haber.id,
					'debit':0,
					'credit':line.provisiones_vaca,
					'name':'Provision - ' + self.payslip_run_id.name,
					'partner_id':line.employee_id.address_home_id.id if line.employee_id.address_home_id else None
				})
		
		return move_lines

	def get_provisions_wizard(self):
		move_lines = self.get_move_lines()
		total_debit = total_credit = 0
		for line in move_lines:
			total_debit += line['debit']
			total_credit += line['credit']
		return {
			'name': 'Generar Asiento Contable',
			'type': 'ir.actions.act_window',
			'res_model': 'hr.provisions.wizard',
			'views': [(self.env.ref('hr_provisions.hr_provisions_wizard_form').id, 'form')],
			'context': {'default_credit': total_credit,
						'default_debit': total_debit,
						'move_lines': move_lines},
			'target': 'new'
		}

	def get_provisiones_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'provisiones.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########CTS############
		worksheet = workbook.add_worksheet("CTS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,11, "PROVISIONES-CTS", formats['especial3'])
		worksheet.write(3,0,"Periodo",formats['boldbord'])
		worksheet.write(3,1,self.payslip_run_id.name,formats['especial1'])

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",formats['boldbord'])
		worksheet.write(x,1,"EMPLEADO",formats['boldbord'])
		worksheet.write(x,2,"FECHA INGRESO",formats['boldbord'])
		worksheet.write(x,3,"DISTRIBUCION ANALITICA",formats['boldbord'])
		worksheet.write(x,4,"REMUNERACION BASICA",formats['boldbord'])
		worksheet.write(x,5,"ASIGNACION FAMILIAR",formats['boldbord'])
		worksheet.write(x,6,"COMISION",formats['boldbord'])
		worksheet.write(x,7,"BONIFICACION",formats['boldbord'])
		worksheet.write(x,8,"PROM. HORAS EXTRAS",formats['boldbord'])
		worksheet.write(x,9,"1/6 GRATIFICACION",formats['boldbord'])
		worksheet.write(x,10,"PROVISIONES CTS",formats['boldbord'])
		worksheet.write(x,11,"TOTAL CTS ADIC.",formats['boldbord'])
		x=6

		for line in self.cts_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',formats['especial1'])
			worksheet.write(x,1,line.employee_id.name if line.employee_id else '',formats['especial1'])
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',formats['dateformat'])
			worksheet.write(x,3,line.distribution_id or '', formats['especial1'])
			worksheet.write(x,4,line.basico if line.basico else 0,formats['numberdos'])
			worksheet.write(x,5,line.asignacion if line.asignacion else 0,formats['numberdos'])
			worksheet.write(x,6,line.commission if line.commission else 0,formats['numberdos'])
			worksheet.write(x,7,line.bonus if line.bonus else 0,formats['numberdos'])
			worksheet.write(x,8,line.extra_hours if line.extra_hours else 0,formats['numberdos'])
			worksheet.write(x,9,line.un_sexto_grati if line.un_sexto_grati else 0,formats['numberdos'])
			worksheet.write(x,10,line.provisiones_cts if line.provisiones_cts else 0,formats['numberdos'])
			worksheet.write(x,11,line.total_cts if line.total_cts else 0,formats['numberdos'])
			x += 1

		widths = [12,38,13,16,13,15,15,15,15,15,13,11]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		##########GRATIFICACION############
		worksheet = workbook.add_worksheet("GRATIFICACION")
		worksheet.set_tab_color('green')

		worksheet.merge_range(1,0,1,12, "PROVISIONES-GRATIFICACION", formats['especial3'])
		worksheet.write(3,0,"Periodo",formats['boldbord'])
		worksheet.write(3,1,self.payslip_run_id.name,formats['especial1'])

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",formats['boldbord'])
		worksheet.write(x,1,"EMPLEADO",formats['boldbord'])
		worksheet.write(x,2,"FECHA INGRESO",formats['boldbord'])
		worksheet.write(x,3,"DISTRIBUCION ANALITICA",formats['boldbord'])
		worksheet.write(x,4,"REMUNERACION BASICA",formats['boldbord'])
		worksheet.write(x,5,"ASIGNACION FAMILIAR",formats['boldbord'])
		worksheet.write(x,6,"COMISION",formats['boldbord'])
		worksheet.write(x,7,"BONIFICACION",formats['boldbord'])
		worksheet.write(x,8,"PROM. HORAS EXTRAS",formats['boldbord'])
		worksheet.write(x,9,"PROVISIONES GRATIFICACION",formats['boldbord'])
		worksheet.write(x,10,"BONIFICACION DE GRATIFICACION",formats['boldbord'])
		worksheet.write(x,11,"TOTAL",formats['boldbord'])
		worksheet.write(x,12,"TOTAL GRATIFICACION ADIC.",formats['boldbord'])
		x=6

		for line in self.grati_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',formats['especial1'])
			worksheet.write(x,1,line.employee_id.name if line.employee_id else '',formats['especial1'])
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',formats['dateformat'])
			worksheet.write(x,3,line.distribution_id or '', formats['especial1'])
			worksheet.write(x,4,line.basico if line.basico else 0,formats['numberdos'])
			worksheet.write(x,5,line.asignacion if line.asignacion else 0,formats['numberdos'])
			worksheet.write(x,6,line.commission if line.commission else 0,formats['numberdos'])
			worksheet.write(x,7,line.bonus if line.bonus else 0,formats['numberdos'])
			worksheet.write(x,8,line.extra_hours if line.extra_hours else 0,formats['numberdos'])
			worksheet.write(x,9,line.provisiones_grati if line.provisiones_grati else 0,formats['numberdos'])
			worksheet.write(x,10,line.boni_grati if line.boni_grati else 0,formats['numberdos'])
			worksheet.write(x,11,line.total if line.total else 0,formats['numberdos'])
			worksheet.write(x,12,line.total_grati if line.total_grati else 0,formats['numberdos'])
			x += 1

		widths = [12,38,13,15,13,15,15,15,15,15,16,11,15]
		worksheet = ReportBase.resize_cells(worksheet, widths)

		##########VACACIONES############
		worksheet = workbook.add_worksheet("VACACIONES")
		worksheet.set_tab_color('orange')

		worksheet.merge_range(1,0,1,10, "PROVISIONES-VACACIONES", formats['especial3'])
		worksheet.write(3,0,"Periodo",formats['boldbord'])
		worksheet.write(3,1,self.payslip_run_id.name,formats['especial1'])

		x = 5
		worksheet.write(x,0,"NUMERO DE DOCUMENTO",formats['boldbord'])
		worksheet.write(x,1,"EMPLEADO",formats['boldbord'])
		worksheet.write(x,2,"FECHA INGRESO",formats['boldbord'])
		worksheet.write(x,3,"DISTRIBUCION ANALITICA",formats['boldbord'])
		worksheet.write(x,4,"REMUNERACION BASICA",formats['boldbord'])
		worksheet.write(x,5,"ASIGNACION FAMILIAR",formats['boldbord'])
		worksheet.write(x,6,"COMISION",formats['boldbord'])
		worksheet.write(x,7,"BONIFICACION",formats['boldbord'])
		worksheet.write(x,8,"PROM. HORAS EXTRAS",formats['boldbord'])
		worksheet.write(x,9,"PROVISIONES VACACIONES",formats['boldbord'])
		worksheet.write(x,10,"TOTAL VACACIONES ADIC.",formats['boldbord'])
		x=6

		for line in self.vaca_lines:
			worksheet.write(x,0,line.nro_doc if line.nro_doc else '',formats['especial1'])
			worksheet.write(x,1,line.employee_id.name if line.employee_id else '',formats['especial1'])
			worksheet.write(x,2,line.fecha_ingreso if line.fecha_ingreso else '',formats['dateformat'])
			worksheet.write(x,3,line.distribution_id or '', formats['especial1'])
			worksheet.write(x,4,line.basico if line.basico else 0,formats['numberdos'])
			worksheet.write(x,5,line.asignacion if line.asignacion else 0,formats['numberdos'])
			worksheet.write(x,6,line.commission if line.commission else 0,formats['numberdos'])
			worksheet.write(x,7,line.bonus if line.bonus else 0,formats['numberdos'])
			worksheet.write(x,8,line.extra_hours if line.extra_hours else 0,formats['numberdos'])
			worksheet.write(x,9,line.provisiones_vaca if line.provisiones_vaca else 0,formats['numberdos'])
			worksheet.write(x,10,line.total_vaca if line.total_vaca else 0,formats['numberdos'])
			x += 1

		widths = [12,38,13,15,15,15,15,15,13,13,12]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		
		workbook.close()

		f = open(route + 'provisiones.xlsx', 'rb')
		return self.env['popup.it'].get_file('Provisiones - %s.xlsx' % self.payslip_run_id.name,base64.encodestring(b''.join(f.readlines())))

class HrProvisionesCtsLine(models.Model):
	_name = 'hr.provisiones.cts.line'
	_description = 'Provisiones Cts Line'

	provision_id = fields.Many2one('hr.provisiones', ondelete='cascade')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	distribution_id = fields.Char('Distribucion Analitica')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')
	un_sexto_grati = fields.Float('1/6 Gratificacion')

	commission = fields.Float(string='Comision')
	bonus = fields.Float(string='Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extra')

	@api.depends('basico','asignacion','commission','bonus','extra_hours','un_sexto_grati','total_cts')
	def _get_prov_cts(self):
		for record in self:
			amount = (record.basico + record.asignacion + record.commission+ record.bonus+ record.extra_hours+ record.un_sexto_grati + record.total_cts)/12
			divider = 2 if record.contract_id.labor_regime == 'small' else 1
			record.provisiones_cts = self.env['report.base'].custom_round(amount/divider, 2)

	provisiones_cts = fields.Float('Provisiones CTS',compute="_get_prov_cts")
	total_cts = fields.Float('Total CTS Adic.')

	def get_wizard(self):
		return self.env['cts.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)


class CtsLineWizard(models.Model):
	_name = 'cts.line.wizard'
	_description = 'Cts Line Wizard'

	conceptos_lines = fields.One2many('cts.conceptos','cts_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.cts.line', ondelete='cascade')

	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['cts.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'cts.line.wizard',
			'views':[[self.env.ref('hr_provisions.cts_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.cts.line'].browse(self.line_id.id).write({'total_cts':total})
		else:
			self.env['hr.provisiones.cts.line'].browse(self.line_id.id).write({'total_cts':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).cts_lines.refresh()


class CtsConceptos(models.Model):
	_name = 'cts.conceptos'
	_description = 'Cts Conceptos'
	
	cts_line_id = fields.Many2one('cts.line.wizard', ondelete='cascade')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')

class HrProvisionesGratiLine(models.Model):
	_name = 'hr.provisiones.grati.line'
	_description = 'Provisiones Grati Line'

	provision_id = fields.Many2one('hr.provisiones', ondelete='cascade')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	distribution_id = fields.Char('Distribucion Analitica')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')

	commission = fields.Float(string='Comision')
	bonus = fields.Float(string='Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extra')

	@api.depends('basico','asignacion','commission','bonus','extra_hours','total_grati')
	def _get_prov_grati(self):
		for record in self:
			amount = (record.basico + record.asignacion + record.commission+ record.bonus+ record.extra_hours+ record.total_grati)/6
			divider = 2 if record.contract_id.labor_regime == 'small' else 1
			record.provisiones_grati = record.env['report.base'].custom_round(amount/divider, 2)

	provisiones_grati = fields.Float('Provisiones Gratificacion',compute="_get_prov_grati")
	tasa = fields.Float('Tasa')

	@api.depends('provisiones_grati','tasa')
	def _get_boni(self):
		for record in self:
			record.boni_grati = self.env['report.base'].custom_round(record.provisiones_grati * record.tasa/100, 2)

	boni_grati = fields.Float('Bonificacion de Gratificacion',compute="_get_boni")

	@api.depends('provisiones_grati','boni_grati')
	def _get_total(self):
		for record in self:
			record.total = record.provisiones_grati + record.boni_grati

	total = fields.Float('Total',compute="_get_total")
	total_grati = fields.Float('Total Grat. Adic.')

	def get_wizard(self):
		return self.env['grati.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)

class GratiLineWizard(models.Model):
	_name = 'grati.line.wizard'
	_description = 'Grati Line Wizard'

	conceptos_lines = fields.One2many('grati.conceptos','grati_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.grati.line', ondelete='cascade')

	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['grati.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'grati.line.wizard',
			'views':[[self.env.ref('hr_provisions.grati_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.grati.line'].browse(self.line_id.id).write({'total_grati':total})
		else:
			self.env['hr.provisiones.grati.line'].browse(self.line_id.id).write({'total_grati':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).grati_lines.refresh()

class GratiConceptos(models.Model):
	_name = 'grati.conceptos'
	_description = 'Grati Conceptos'
	
	grati_line_id = fields.Many2one('grati.line.wizard', ondelete='cascade')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')

class HrProvisionesVacaLine(models.Model):
	_name = 'hr.provisiones.vaca.line'
	_description = 'Provisiones Vaca Line'

	provision_id = fields.Many2one('hr.provisiones', ondelete='cascade')
	nro_doc = fields.Char('Numero de Documento')
	employee_id = fields.Many2one('hr.employee','Empleado')
	contract_id = fields.Many2one('hr.contract','Contrato')
	fecha_ingreso = fields.Date('Fecha Ingreso')
	distribution_id = fields.Char('Distribucion Analitica')
	basico = fields.Float('Remuneracion Basica')
	asignacion = fields.Float('Asignacion Familiar')

	commission = fields.Float(string='Comision')
	bonus = fields.Float(string='Bonificacion')
	extra_hours = fields.Float(string='Prom. Horas Extra')

	@api.depends('basico','asignacion','commission','bonus','extra_hours','total_vaca')
	def _get_prov_vaca(self):
		for record in self:
			amount = (record.basico + record.asignacion + record.commission+ record.bonus+ record.extra_hours+ record.total_vaca)/12
			divider = 2 if record.contract_id.labor_regime == 'small' else 1
			record.provisiones_vaca = self.env['report.base'].custom_round(amount/divider, 2)

	provisiones_vaca = fields.Float('Provisiones Vacacion',compute="_get_prov_vaca")
	total_vaca = fields.Float('Total Vac. Adic.')

	def get_wizard(self):
		return self.env['vaca.line.wizard'].get_wizard(self.employee_id.id,self.provision_id.id,self.id)

class VacaLineWizard(models.Model):
	_name = 'vaca.line.wizard'
	_description = 'Vaca Line Wizard'

	conceptos_lines = fields.One2many('vaca.conceptos','vaca_line_id')
	employee_id = fields.Many2one('hr.employee')
	provision_id = fields.Many2one('hr.provisiones')
	line_id = fields.Many2one('hr.provisiones.vaca.line', ondelete='cascade')

	def get_wizard(self,employee_id,provision_id,line_id):
		res_id = self.env['vaca.line.wizard'].search([('line_id','=',line_id)],limit=1)
		res_id = res_id.id if res_id else self.id
		return {
			'name':_('Conceptos Adicionales'),
			'type':'ir.actions.act_window',
			'res_id':res_id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'vaca.line.wizard',
			'views':[[self.env.ref('hr_provisions.vaca_line_wizard').id,'form']],
			'target':'new',
			'context':{
				'default_employee_id':employee_id,
				'default_provision_id':provision_id,
				'default_line_id':line_id
			}
		}

	def add_concept(self):
		total = 0
		if self.conceptos_lines:
			for line in self.conceptos_lines:
				total += line.monto
			self.env['hr.provisiones.vaca.line'].browse(self.line_id.id).write({'total_vaca':total})
		else:
			self.env['hr.provisiones.vaca.line'].browse(self.line_id.id).write({'total_vaca':0}) 
		return self.env['hr.provisiones'].browse(self.provision_id.id).vaca_lines.refresh()

class VacaConceptos(models.Model):
	_name = 'vaca.conceptos'
	_description = 'Vaca Conceptos'
	
	vaca_line_id = fields.Many2one('vaca.line.wizard', ondelete='cascade')
	concepto = fields.Many2one('hr.salary.rule','Concepto')
	monto = fields.Float('Monto')
