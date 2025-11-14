# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	aux_currency_rate = fields.Float(default=1,digits=(16,4))

	@api.onchange('invoice_date','tc_per')
	def _get_currency_rate(self):
		if self.tc_per:
			date_currency = self.invoice_date if self.invoice_date else fields.Date.today()
			cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.currency_rate = cu_rate.sale_type
				self.aux_currency_rate = cu_rate.sale_type
				if self.is_invoice(include_receipts=True):
					for line in self.line_ids:
						line.tc = cu_rate.sale_type

	@api.onchange('tc_per','date')
	def _get_currency_rate_date(self):
		if not self.tc_per:
			date_currency = self.date if self.date else fields.Date.today()
			cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.currency_rate = cu_rate.sale_type
				self.aux_currency_rate = cu_rate.sale_type
				if self.is_invoice(include_receipts=True):
					for line in self.line_ids:
						line.tc = cu_rate.sale_type

	def write(self,vals):
		if 'aux_currency_rate' in vals:
			vals.update({'currency_rate':vals['aux_currency_rate']})
		return super(AccountMove,self).write(vals)

	def post(self):
		res = super(AccountMove,self).post()
		for move in self:
			if move.is_invoice(include_receipts=True):
				for line in move.line_ids:
					line.tc = move.currency_rate
		return res