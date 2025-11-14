# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, ValidationError

class CurrencyRateUpdateNow(models.TransientModel):
	_name = "currency.rate.update.now"
	
	rate_update_id = fields.Many2one("pe.currency.rate.update.service", "Rate update", 
									 default = lambda self: self.env.context.get('active_ids',[]) and self.env.context.get('active_ids',[])[0] or False)
	date = fields.Date(string="Fecha",readonly=True,default=fields.Date.context_today)
	purchase_type = fields.Float(string='Tipo Compra',digits=(16, 3),required=True)
	sale_type = fields.Float(string='Tipo Venta',digits=(16, 3),required=True)

	def update_now(self):
		rate_obj = self.env['res.currency.rate']
		currency = self.env.ref('base.USD')
		if currency:
			rate_search = rate_obj.search([
						('name', '=', self.date),
						('currency_id', '=', currency.id),
						('company_id','=',self.env.company.id)
					],limit=1)

			if rate_search:
				rate_search.write({
					'rate': 1.0 / self.sale_type,
					'sale_type': self.sale_type,
					'purchase_type': self.purchase_type,
				})
			else:
				rate_obj.create({
					'currency_id': currency.id,
					'rate': 1.0 / self.sale_type,
					'name': self.date,
					'sale_type': self.sale_type,
					'purchase_type': self.purchase_type,
					'company_id': self.env.company.id
				})

			return self.env['popup.it'].get_message(u'SE ACTUALIZÓ CORRECTAMENTE EL TC PARA EL DIA %s'%(self.date.strftime('%Y/%m/%d')))