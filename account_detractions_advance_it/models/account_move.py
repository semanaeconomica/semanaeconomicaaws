# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	detraction_percent_id = fields.Many2one('detractions.catalog.percent',string='Bien o Servicio')
	percentage = fields.Float(related='detraction_percent_id.percentage',readonly=True)

	@api.onchange('detraction_percent_id','amount_total')
	def onchange_detraction_percent_id(self):
		for move in self:
			if move.detraction_percent_id:
				move.code_operation = move.detraction_percent_id.code
				move.detra_amount = round(move.amount_total * move.detraction_percent_id.percentage)
			else:
				move.detra_amount = 0

	def post(self):
		res = super(AccountMove, self).post()
		for move in self:
			if move.detraction_percent_id:
				move.detra_amount = round(move.amount_total * move.detraction_percent_id.percentage)
			else:
				move.detra_amount = 0
		return res

	def create_detraccion_gastos(self):
		###SE CAMBIO POR FUSION
		context = {'invoice_id': self.id,'default_fecha': self.date ,
		'default_monto':self.detra_amount}
		return {
				'type': 'ir.actions.act_window',
				'name': "Generar Detracción",
				'view_type': 'form',
				'view_mode': 'form',
				'context': context,
				'res_model': 'account.detractions.wizard',
				'target': 'new',
		}