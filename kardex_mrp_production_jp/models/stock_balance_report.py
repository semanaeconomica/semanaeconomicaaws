# -*- coding:utf-8 -*-
from odoo import api, fields, models

class StockBalanceReport(models.Model):
	_inherit = 'stock.balance.report'

	def get_balance_view(self):
		self.search([]).unlink()
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
		lst_locations = locat_ids.ids
		productos='{'
		almacenes='{'
		lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		if len(lst_products) == 0:
			raise osv.except_osv('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'
		date_ini = '01/01/%d' % fields.Date.today().year
		date_fin = fields.Date.today()
		self.env.cr.execute("""
			select 
			origen AS "Ubicación Origen",
			destino AS "Ubicación Destino",
			almacen AS "Almacén",
			vstf.motivo_guia::varchar AS "Tipo de operación",
			categoria as "Categoria",
			producto as "Producto",
			cod_pro as "Codigo P.",
			unidad as "unidad",
			vstf.fecha as "Fecha",
			vstf.name as "Doc. Almacén",
			vstf.entrada as "Entrada",
			vstf.salida as "Salida",
			categoria_id,
			product_id,
			almacen_id
			from
			(
			select u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.guia as motivo_guia, categoria, producto, cod_pro, unidad, vst_kardex_fisico.date as fecha, vst_kardex_fisico.name, vst_kardex_fisico.product_qty as entrada, 0 as salida, vst_kardex_fisico.estado, product_id,location_dest_id as almacen_id, categoria_id from vst_kardex_fisico()
			union all
			select u_origen as origen, u_destino as destino, u_origen as almacen, vst_kardex_fisico.guia as motivo_guia, categoria, producto, cod_pro, unidad, vst_kardex_fisico.date as fecha, vst_kardex_fisico.name, 0 as entrada, vst_kardex_fisico.product_qty as salida, vst_kardex_fisico.estado, product_id,location_id as almacen_id, categoria_id from vst_kardex_fisico()
			) as vstf
			where vstf.fecha::date >='""" +str(date_ini)+ """' and vstf.fecha::date <='""" +str(date_fin)+ """'
			and vstf.product_id in """ +str(tuple(s_prod))+ """
			and vstf.almacen_id in """ +str(tuple(s_loca))+ """
			and vstf.estado = 'done'
			order by
			almacen,producto,vstf.fecha;
		""")
		
		for line in self.env.cr.fetchall():
			Category_1 = self.env['product.category'].browse(line[12])
			Product = self.env['product.product'].browse(line[13])
			Location = self.env['stock.location'].browse(line[14])
			Category_2 = Category_3 = None
			if Category_1 and Category_1.parent_id:
				Category_2 = self.env['product.category'].browse(Category_1.parent_id.id)
				if Category_2 and Category_2.parent_id:
					Category_3 = self.env['product.category'].browse(Category_2.parent_id.id)
			if Location.location_id.name != 'Virtual Locations':
				self.create({
							'producto': line[5],
							'codigo': line[6],
							'almacen': line[2],
							'entrada': line[10],
							'salida': line[11],
							'saldo': line[10] - line[11],
							'unidad': Product.uom_id.name or '',
							'marca': Product.product_brand_id.name or '',
							'categoria_1': Category_1.complete_name if Category_1 else '',
							'categoria_2': Category_2.complete_name if Category_2 else '',
							'categoria_3': Category_3.complete_name if Category_3 else '',
						})
		return {
			'name': 'Reporte de Saldos',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.balance.report',
			'view_mode': 'tree,pivot,graph',
			'views': [(False, 'tree'), (False, 'pivot'), (False, 'graph')]
		}