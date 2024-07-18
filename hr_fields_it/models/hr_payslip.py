# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	income = fields.Monetary(compute='_compute_basic_net', string='Ingresos')
	worker_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Trabajador')
	net_discounts = fields.Monetary(compute='_compute_basic_net', string='Descuentos al Neto')
	net_to_pay = fields.Monetary(compute='_compute_basic_net', string='Neto a Pagar')
	employer_contributions = fields.Monetary(compute='_compute_basic_net', string='Aportes Empleador')
	holidays = fields.Integer(string='Dias Feriados y Domingos')

	@api.model
	def create(self, vals):
		rec = super(HrPayslip, self).create(vals)
		rec.generate_inputs_and_wd_lines()
		return rec

	def get_dlabs(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		return self.date_to.day - self.holidays - sum(DNLAB.mapped('number_of_days')) - sum(DSUB.mapped('number_of_days')) - sum(DVAC.mapped('number_of_days'))

	def generate_inputs_and_wd_lines(self, recompute=False):
		for payslip in self:
			if recompute:
				input_type_lines = payslip.input_line_ids.mapped('input_type_id')
				wd_type_lines = payslip.worked_days_line_ids.mapped('wd_type_id')
			else:
				payslip.input_line_ids.unlink()
				payslip.worked_days_line_ids.unlink()
			input_types = payslip.struct_id.mapped('input_line_type_ids')
			wd_types = payslip.struct_id.mapped('wd_types_ids')
			for type in input_types:
				vals = {'input_type_id': type.id,
						'amount': 0,
						'payslip_id': payslip.id,
						'code': type.code,
						'contract_id': payslip.contract_id.id,
						'struct_id': payslip.struct_id.id}
				if recompute and type not in input_type_lines:
					self.env['hr.payslip.input'].create(vals)
				if not recompute:
					self.env['hr.payslip.input'].create(vals)
			for type in wd_types:
				vals = {'wd_type_id': type.id,
						'payslip_id': payslip.id,
						'number_of_days': type.days,
						'number_of_hours': type.hours}
				if recompute and type not in wd_type_lines:
					self.env['hr.payslip.worked_days'].create(vals)
				if not recompute:
					self.env['hr.payslip.worked_days'].create(vals)

	def compute_wds(self):
		for record in self:
			MainParameter = self.env['hr.main.parameter'].get_main_parameter()
			Holidays = self.env['hr.holidays'].search([('date', '>=', record.date_from),
													   ('date', '<=', record.date_to),
													   ('workday_id', '=', record.contract_id.workday_id.id)])
			record.holidays = len(Holidays)
			if not MainParameter.payslip_working_wd:
				raise UserError('Falta configurar un Worked Day para Dias Laborados en Parametros Principales de Nomina')
			WDLine = record.worked_days_line_ids.filtered(lambda line: line.wd_type_id == MainParameter.payslip_working_wd)
			Contract = self.env['hr.contract'].get_first_contract(record.employee_id, record.contract_id)
			if Contract.date_start > record.date_from and Contract.date_start <= record.date_to:
				result = record.date_to.day - Contract.date_start.day + 1
				WDLine.number_of_days = result
		return self.env['popup.it'].get_message('Se calculo correctamente')

	def _compute_basic_net(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for payslip in self:
			payslip.basic_wage = 0
			payslip.income = payslip._get_salary_line_total(MainParameter.income_sr_id.code)
			payslip.worker_contributions = payslip._get_salary_line_total(MainParameter.worker_contributions_sr_id.code)
			payslip.net_wage = payslip._get_salary_line_total(MainParameter.net_sr_id.code)
			payslip.net_discounts = payslip._get_salary_line_total(MainParameter.net_discounts_sr_id.code)
			payslip.net_to_pay = payslip._get_salary_line_total(MainParameter.net_to_pay_sr_id.code)
			payslip.employer_contributions = payslip._get_salary_line_total(MainParameter.employer_contributions_sr_id.code)