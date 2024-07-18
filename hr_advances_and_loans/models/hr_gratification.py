# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *

class HrGratification(models.Model):
	_inherit = 'hr.gratification'

	def import_advances(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.grat_advance_input_id:
			raise UserError('No se ha configurado un input para Adelantos de Gratificacion en Parametros Generales en la pestaña Gratificacion')
		Lot = self.payslip_run_id
		for line in self.line_ids:
			sql = """
				select sum(ha.amount) as amount,
				ha.employee_id
				from hr_advance ha
				inner join hr_advance_type hat on hat.id = ha.advance_type_id
				where ha.discount_date >= '{0}' and
					  ha.discount_date <= '{1}' and
					  ha.employee_id = {2} and
					  ha.state = 'not payed' and
					  hat.input_id = {3}
				group by ha.employee_id
				""".format(Lot.date_start, Lot.date_end, line.employee_id.id, MainParameter.grat_advance_input_id.id)
			self._cr.execute(sql)
			data = self._cr.dictfetchall()
			if data:
				line.advance_amount = data[0]['amount']
				line.total = line.total_grat + line.bonus_essalud - line.advance_amount
			self.env['hr.advance'].search([('discount_date', '>=', Lot.date_start),
										   ('discount_date', '<=', Lot.date_end),
										   ('employee_id', '=', line.employee_id.id),
										   ('state', '=', 'not payed'),
										   ('advance_type_id.input_id', '=', MainParameter.grat_advance_input_id.id)]).turn_paid_out()
		return self.env['popup.it'].get_message('Se importo exitosamente')

	def set_amounts(self, line_ids, Lot, MainParameter):
		super(HrGratification, self).set_amounts(line_ids, Lot, MainParameter)
		inp_adv = MainParameter.grat_advance_input_id
		for line in line_ids:
			Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == line.employee_id)
			adv_line = Slip.input_line_ids.filtered(lambda inp: inp.input_type_id == inp_adv)
			adv_line.amount = line.advance_amount


class HrGratificationLine(models.Model):
	_inherit = 'hr.gratification.line'

	advance_amount = fields.Float(string='Monto de Adelanto')