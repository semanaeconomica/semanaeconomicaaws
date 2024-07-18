# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	aux_type_change = fields.Float(default=1,digits=(16,4))

	@api.onchange('payment_date','currency_id')
	def _get_currency_rate(self):
		if not self.is_personalized_change:
			cu_rate = self.env['res.currency.rate'].search([('name','=',self.payment_date),('company_id','=',self.company_id.id)],limit=1)
			if cu_rate:
				self.type_change = cu_rate.sale_type
				self.aux_type_change = cu_rate.sale_type

	@api.model
	def create(self,vals):
		if 'aux_type_change' in vals:
			vals.update({'type_change':vals['aux_type_change']})
		return super(AccountPayment,self).create(vals)