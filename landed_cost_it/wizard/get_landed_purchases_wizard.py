# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class GetLandedPurchases(models.TransientModel):
	_name = "get.landed.purchases.wizard"
	
	landed_id = fields.Many2one('landed.cost.it',string='Gasto Vinculado')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	purchases = fields.Many2many('landed.purchase.book','get_purchase_landed_book_rel','purchase_id','get_landed_purchase_id',string=u'Purchases', required=True)
		
	def insert(self):
		vals=[]
		for purchase in self.purchases:
			val = {
				'landed_id': self.landed_id.id,
				'purchase_id': purchase.purchase_id.id,
				'purchase_date': purchase.purchase_date,
				'name': purchase.name,
				'partner_id': purchase.partner_id.id,
				'product_id': purchase.product_id.id,
				'price_total_signed': purchase.price_total_signed,
				'tc': purchase.tc,
				'currency_id': purchase.currency_id.id,
				'price_total': purchase.price_total,
				'company_id': purchase.company_id.id,
			}
			vals.append(val)
		self.env['landed.cost.purchase.line'].create(vals)
		self.landed_id._change_flete()