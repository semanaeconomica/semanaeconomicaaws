# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from datetime import datetime, timedelta
class main_parameter(models.Model):
	_inherit = 'main.parameter'

	anio_saldos = fields.Integer(u'Año Inicio Operaciones - Saldo')

class StockBalanceReport(models.Model):
	_name = 'stock.balance.report'
	_description = 'Balance Report'

	producto = fields.Many2one('product.product',string='Producto',store=True)
	codigo = fields.Char(related='producto.default_code',string='Cod. Producto',store=True)
	almacen = fields.Many2one('stock.location',string=u'Almacén',store=True)
	entrada = fields.Float(string='Stock', digits=(12,2),store=True)
	salida = fields.Float(string='Salida', digits=(12,2),store=True)
	saldo = fields.Float(string='Disponible', digits=(12,2),store=True)
	unidad = fields.Many2one(related='producto.uom_id',string='Unidad',store=True)
	categoria_1 = fields.Char(related='producto.categ_id.name',string='Categoria 1',store=True)
	categoria_2 = fields.Char(related='producto.categ_id.parent_id.name',string='Categoria 2',store=True)
	categoria_3 = fields.Char(related='producto.categ_id.parent_id.parent_id.name',string='Categoria 3',store=True)

	reservado = fields.Float(string='Reservado', digits=(12,2),store=True)
	product_id = fields.Many2one('product.product','Producto',store=True)
	almacen_id = fields.Many2one('stock.location','Almacen',store=True)

	def get_balance_view(self):
		self.search([]).unlink()
		s_prod = [-1,-1,-1]
		s_loca = [-1,-1,-1]
		locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
		lst_locations = locat_ids.ids
		productos='{'
		almacenes='{'
		lst_products = self.env['product.product'].with_context(active_test=False).search([]).ids
		if len(lst_products) == 0:
			raise UserError('Alerta','No existen productos seleccionados')

		for producto in lst_products:
			productos=productos+str(producto)+','
			s_prod.append(producto)
		productos=productos[:-1]+'}'
		for location in lst_locations:
			almacenes=almacenes+str(location)+','
			s_loca.append(location)
		almacenes=almacenes[:-1]+'}'

		config = self.env['kardex.parameter'].search([('company_id','=',self.env.company.id)])

		date_fin = self.env.context['date_final'] if 'date_final' in self.env.context else fields.Date.context_today(self)
		date_ini = '%d-01-01' % ( config._get_anio_start(date_fin.year) )

		kardex_save_obj = self.env['kardex.save'].search([('company_id','=',self.env.company.id),('state','=','done'),('name.date_end','<',date_fin),('name.fiscal_year_id.name','=',str(date_fin.year) )]).sorted(lambda l: l.name.code , reverse=True)
		if len(kardex_save_obj)>0:
			kardex_save_obj = kardex_save_obj[0]
			date_ini = kardex_save_obj.name.date_end + timedelta(days=1)
			
		data={}


		if kardex_save_obj:
			for alm in kardex_save_obj.lineas:
				if (alm.almacen.id,alm.producto.id) in data:
					data[(alm.almacen.id,alm.producto.id)][2] += alm.stock
				else:					
					self.env.cr.execute(""" select sum(product_uom_qty) 
						from stock_move_line 
						inner join stock_production_lot  on stock_production_lot.id = stock_move_line.lot_id 
						where 
						stock_move_line.location_id = """ +str(alm.almacen.id)+ """
						and stock_move_line.product_id = """ +str(alm.producto.id)+ """ and 
						stock_move_line.state in ('partially_available','assigned') """)
					cont1 = 0
					for ex in self.env.cr.fetchall():
						cont1 = ex[0]
					data[(alm.almacen.id,alm.producto.id)] = [alm.almacen.id,alm.producto.id,alm.stock,cont1]


		self.env.cr.execute("""
			select 
			max(origen) AS "Ubicación Origen",
			max(destino) AS "Ubicación Destino",
			max(almacen) AS "Almacén",
			max(vstf.motivo_guia)::varchar AS "Tipo de operación",
			max(categoria) as "Categoria",
			producto as "Producto",
			cod_pro as "Codigo P.",
			max(unidad) as "unidad",
			max(vstf.fecha) as "Fecha",
			max(vstf.name) as "Doc. Almacén",
			sum(vstf.entrada) as "Entrada",
			sum(vstf.salida) as "Salida",
			categoria_id,
			p_id,
			alm_id,
			( select sum(product_uom_qty) from stock_move_line where location_id = max(vstf.almacen_id) and product_id = vstf.p_id and state in ('partially_available','assigned') ) as "Reservado"
			from
			(
			select location_dest_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_destino as almacen, vst_kardex_fisico.product_qty as entrada, 0 as salida,vst_kardex_fisico.id  as stock_move,vst_kardex_fisico.guia as motivo_guia, producto,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id,location_dest_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			union all
			select location_id as alm_id, product_id as p_id, categoria_id, vst_kardex_fisico.date as fecha,u_origen as origen, u_destino as destino, u_origen as almacen, 0 as entrada, vst_kardex_fisico.product_qty as salida,vst_kardex_fisico.id  as stock_move ,vst_kardex_fisico.guia as motivo_guia ,producto ,vst_kardex_fisico.estado,vst_kardex_fisico.name, cod_pro, categoria, unidad,product_id, location_id as almacen_id from vst_kardex_fisico_lote() as vst_kardex_fisico where company_id = """+str(self.env.company.id)+"""
			) as vstf
			where vstf.fecha::date >='""" +str(date_ini)+ """' and vstf.fecha::date <='""" +str(date_fin)+ """'
			and vstf.product_id in """ +str(tuple(s_prod))+ """
			and vstf.almacen_id in """ +str(tuple(s_loca))+ """
			and vstf.estado = 'done'
			group by
			producto,cod_pro,categoria_id, p_id, alm_id;
		""")
		
		for line in self.env.cr.fetchall():
			if (line[14],line[13]) in data:
				data[(line[14],line[13])][2] += (line[10] or 0) - (line[11] or 0)
			else:
				data[(line[14],line[13])] = [line[14],line[13], (line[10] or 0) - (line[11] or 0) , line[15]]


		for final in data:
			self.create({
						'producto': data[final][1],
						'almacen': data[final][0],
						'entrada': data[final][2],
						'salida': 0,
						'saldo': data[final][2]- (data[final][3] or 0),
						'reservado': data[final][3],
						'product_id': data[final][1],
						'almacen_id': data[final][0],
					})

		return {
			'name': 'Reporte de Saldos',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.balance.report',
			'view_mode': 'tree,pivot,graph',
			'views': [(False, 'tree'), (False, 'pivot'), (False, 'graph')]
		}