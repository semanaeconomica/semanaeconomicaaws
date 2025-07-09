# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ReportMrpBomLine(models.Model):
	_name = 'resport.purchase.order.invoice.it'
	_description = "Reporte para poder crear la vista de rendimiento de ordenes de compra"

	create_date_po = fields.Datetime(string=u'Fecha de creación de Orden de Compra')
	name_po = fields.Char(string=u'Número de Orden de Compra')
	state_po = fields.Selection([
								('draft', 'RFQ'),
								('sent', 'RFQ Envio'),
								('to approve', 'Por Aprobar'),
								('purchase', 'Orden de compra'),
								('done', 'Bloqueado'),
								('cancel', 'Cancelado')
							],string=u'Estado de Orden de Compra')
	create_date_am = fields.Datetime(string=u'Fecha de registro de factura')
	invoice_date_am = fields.Datetime(string=u'Fecha de emisión de factura')
	invoice_date_due_am = fields.Datetime(string=u'Fecha de vencimiento de factura')
	dates_str = fields.Text(string=u'Fechas de pago')
	ref_am = fields.Char(string=u'Número de Factura')
	partner_id = fields.Many2one('res.partner', string=u'Nombre del proveedor')
	product_id = fields.Many2one('product.product', string=u'Producto')
	description_am = fields.Char(string=u'Descripción')
	currency_id = fields.Many2one('res.currency', string=u'Moneda')
	import_aml = fields.Float(string=u'Importe')
	company_id = fields.Many2one('res.company', string=u'Compañía')





	def get_view_orders_report(self, date_start, date_end):
		self.search([]).unlink()
		company_id = self.env.company.id
		query = f"""
					SELECT 
						po.create_date AS create_date_po, 
						po.name AS name_po, 
						po.state AS state_po, 
						am.create_date AS create_date_am, 
						am.invoice_date AS invoice_date_am, 
						am.invoice_date_due AS invoice_date_due_am, 
						string_agg(DISTINCT to_char(aml2.date, 'YYYY-MM-DD'), ',\n ') AS dates_str,
						am.ref AS ref_am, 
						am.partner_id AS partner_id, 
						pol.product_id AS product_id, 
						pol.name AS description_am, 
						am.currency_id AS currency_id, 
						aml.price_total AS import_aml,
						am.company_id AS company_id
						FROM purchase_order_line pol
							LEFT JOIN purchase_order po on po.id=pol.order_id
							LEFT JOIN account_move_line aml on aml.purchase_line_id = pol.id
							LEFT JOIN account_move am on am.id = aml.move_id
							LEFT JOIN account_move_line aml1 on aml1.move_id = am.id and aml1.id!=aml.id
							LEFT JOIN account_full_reconcile afr on afr.id = aml1.full_reconcile_id
							LEFT JOIN account_move_line aml2 on aml2.full_reconcile_id=afr.id and aml2.id!=aml1.id and aml2.id!=aml.id
						WHERE po.create_date BETWEEN '{date_start} 00:00:00' AND '{date_end} 23:59:59' 
						GROUP BY
							po.create_date, 
							po.name, 
							po.state, 
							am.create_date, 
							am.invoice_date, 
							am.invoice_date_due, 
							am.ref, 
							am.partner_id, 
							pol.name, 
							pol.product_id, 
							am.currency_id, 
							aml.price_total,
							am.company_id

		"""
		self._cr.execute(query, (company_id,))  # Usa % para el comodín en SQL

		todos = self.env.cr.fetchall()

		for item in todos:
			data = {
				'create_date_po': item[0],
				'name_po': item[1],
				'state_po': item[2],
				'create_date_am': item[3],
				'invoice_date_am': item[4],
				'invoice_date_due_am': item[5],
				'dates_str': item[6],
				'ref_am': item[7],
				'partner_id': item[8],
				'product_id': item[9],
				'description_am': item[10],
				'currency_id': item[11],
				'import_aml': item[12],
				'company_id': item[13],
			}
			self.env['resport.purchase.order.invoice.it'].sudo().create(data)

		return {
			'name': 'Reporte de Reporte de ordenes de compra',
			'type': 'ir.actions.act_window',
			'res_model': 'resport.purchase.order.invoice.it',
			'view_mode': 'tree',
			'views': [(False, 'tree')]
		}
