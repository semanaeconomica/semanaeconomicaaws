# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class LandedPurchaseBook(models.Model):
	_name = 'landed.purchase.book'
	_description = 'Landed Purchase'
	_auto = False
	
	purchase_id = fields.Many2one('purchase.order.line',string='Compra')
	purchase_date = fields.Date(string='Fecha Pedido')
	name = fields.Char(string='Pedido')
	partner_id = fields.Many2one('res.partner',string='Socio')
	product_id = fields.Many2one('product.product',string='Producto')
	price_total_signed = fields.Float(string='Total Soles',digits=(64,2))
	tc = fields.Float(string='TC',digits=(12,4))
	currency_id = fields.Many2one('res.currency',string='Moneda')
	price_total = fields.Float(string='Total',digits=(64,2))
	company_id = fields.Many2one('res.company',string=u'Compañía')

	@api.model
	def init(self):
		tools.drop_view_if_exists(self._cr, 'landed_purchase_book')
		self._cr.execute("""
			CREATE VIEW landed_purchase_book AS (
				SELECT 
				row_number() OVER () AS id,
				pol.id AS purchase_id,
				DATE(po.date_order) AS purchase_date,
				po.name,
				po.partner_id,
				pol.product_id,
				CASE
					WHEN rc.name <> 'PEN' AND rcr.sale_type IS NOT NULL THEN
					(pol.price_subtotal*rcr.sale_type)
					ELSE pol.price_subtotal
				END AS price_total_signed,
				CASE
					WHEN rcr.sale_type IS NOT NULL THEN rcr.sale_type
					ELSE 1.000
				END AS tc,
				rc.id AS currency_id,
				pol.price_subtotal AS price_total,
				po.company_id
				FROM purchase_order_line pol
				LEFT JOIN purchase_order po ON po.id = pol.order_id
				LEFT JOIN product_product pp ON pp.id = pol.product_id
				LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
				LEFT JOIN res_currency rc ON rc.id = po.currency_id
				LEFT JOIN (SELECT DISTINCT ON (name) name,currency_id, rate, sale_type FROM res_currency_rate
				order by name) rcr ON rcr.currency_id = 2 AND DATE(po.date_order) = rcr.name
				WHERE pt.is_landed_cost = TRUE AND pol.display_type IS NULL AND po.state = 'purchase'
			)""")