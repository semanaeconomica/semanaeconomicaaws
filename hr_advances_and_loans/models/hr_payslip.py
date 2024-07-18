# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def import_advances(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_advance_input_id:
			raise UserError('No se ha configurado un input para Adelantos de Gratificacion en Parametros Generales en la pestaña Gratificacion')
		log = ''
		for record in self:
			sql = """
				select sum(ha.amount) as amount,
				hat.input_id
				from hr_advance ha
				inner join hr_advance_type hat on hat.id = ha.advance_type_id
				where ha.discount_date >= '{0}' and
					  ha.discount_date <= '{1}' and
					  ha.employee_id = {2} and
					  ha.state = 'not payed' and
					  hat.input_id != {3}
				group by hat.input_id
				""".format(record.date_from, record.date_to, record.employee_id.id, MainParameter.grat_advance_input_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			for line in data:
				inp_line = record.input_line_ids.filtered(lambda inp: inp.input_type_id.id == line['input_id'])
				inp_line.amount = line['amount']
			self.env['hr.advance'].search([('discount_date', '>=', record.date_from),
										   ('discount_date', '<=', record.date_to),
										   ('employee_id', '=', record.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.input_id', '!=', MainParameter.grat_advance_input_id.id)]).turn_paid_out()
			if data:
				log += '%s\n' % record.employee_id.name
		if log:
			return self.env['popup.it'].get_message('Se importo adelantos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun adelanto')

	def import_loans(self):
		log = ''
		for record in self:
			sql = """
				select sum(hll.amount) as amount,
				hll.input_id
				from hr_loan_line hll
				where hll.date >= '{0}' and
					  hll.date <= '{1}' and
					  hll.employee_id = {2} and
					  hll.validation = 'not payed'
				group by hll.input_id
				""".format(record.date_from, record.date_to, record.employee_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			for line in data:
				inp_line = record.input_line_ids.filtered(lambda inp: inp.input_type_id.id == line['input_id'])
				inp_line.amount = line['amount']
			self.env['hr.loan.line'].search([('date', '>=', record.date_from),
											('date', '<=', record.date_to),
											('employee_id', '=', record.employee_id.id),
											('validation', '=', 'not payed')]).turn_paid_out()
			if data:
				log += '%s\n' % record.employee_id.name
		if log:
			return self.env['popup.it'].get_message('Se importo prestamos a los siguientes empleados:\n' + log)
		else:
			return self.env['popup.it'].get_message('No se importo ningun prestamo')