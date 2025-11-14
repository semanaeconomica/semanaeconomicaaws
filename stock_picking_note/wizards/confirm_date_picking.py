# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class ConfirmDatePicking(models.TransientModel):
	_name = 'confirm.date.picking'

	pick_id = fields.Many2one('stock.picking')
	date = fields.Datetime(string='Fecha del Kardex',default=lambda r: fields.datetime.now())

	def changed_date_pincking(self):
		self.pick_id.kardex_date = self.date
		return self.pick_id.with_context({'a':True}).button_validate()