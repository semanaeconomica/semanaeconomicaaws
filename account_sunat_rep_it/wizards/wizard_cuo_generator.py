# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date

class CuoGenerator(models.TransientModel):
	_name = "cuo.generator"

	period_id = fields.Many2one('account.period',string='Periodo')

	def generate_cuos(self):
		if not self.period_id:
			raise UserError('El Periodo es un campo Obligatorio')
		sql = """update account_move_line set cuo = id where (date between '%s' and '%s') and (cuo is null or cuo = 0)""" % (self.period_id.date_start.strftime('%Y/%m/%d'),
			self.period_id.date_end.strftime('%Y/%m/%d'))
		self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('Se termino de Generar los CUOs en las lineas contables :)')