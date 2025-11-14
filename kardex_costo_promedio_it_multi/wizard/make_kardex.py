# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs

values = {}

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	def write(selfs,vals):
		t = super(stock_picking,selfs).write(vals)
		for self in selfs:
			self.move_ids_without_package.with_context({'nomore':1}).write({})
		return t

class stock_move(models.Model):
	_inherit = 'stock.move'


	def write(selfs,vals):
		t = super(stock_move,selfs).write(vals)
		for self in selfs:
			self.refresh()
			if self.state == 'done':				
				self.env.cr.execute("""
						 select 
						CASE WHEN sum(ingreso)!= 0 THEN round(sum(debit),6)/sum(ingreso)    ELSE 0 END
						from get_kardex_v(20150101,20500101,'{0,""" +str(self.product_id.id)+ """}'::INT[], (select array_agg(id) from stock_location),"""+str(self.env.company.id)+""") 

						left join stock_location origen on origen.id= get_kardex_v.ubicacion_origen
						left join stock_location destino on destino.id= get_kardex_v.ubicacion_destino
						where coalesce(origen.usage,'gasto_vinculado') <> 'internal' or coalesce(destino.usage,'gasto_vinculado') <> 'internal'
				""")
				rpta = 0
				for i in self.env.cr.fetchall():
					rpta = i[0]
				self.product_id.sudo().standard_price = rpta
		return t


class stock_costo_promedio(models.TransientModel):
	_name = 'stock.costo.promedio'

	def do_rebuild(self):
		for i in self.env['product.product'].search([]):		
			self.env.cr.execute("""
					 select 
					CASE WHEN sum(ingreso)!= 0 THEN round(sum(debit),6)/sum(ingreso)    ELSE 0 END
					from get_kardex_v(20150101,20500101,'{0,""" +str(i.id)+ """}'::INT[], (select array_agg(id) from stock_location),"""+str(self.env.company.id)+""" ) 
					 
						left join stock_location origen on origen.id= get_kardex_v.ubicacion_origen
						left join stock_location destino on destino.id= get_kardex_v.ubicacion_destino
						where coalesce(origen.usage,'gasto_vinculado') <> 'internal' or coalesce(destino.usage,'gasto_vinculado') <> 'internal'
			""")
			rpta = 0
			for elem in self.env.cr.fetchall():
				rpta = elem[0]
			i.sudo().standard_price = rpta


class landed_cost_it(models.Model):
	_inherit = 'landed.cost.it'

	def procesar(self):
		t = super(landed_cost_it,self).procesar()
		for i in self.detalle_ids:	
			self.env.cr.execute("""
					 select 
					CASE WHEN sum(ingreso)!= 0 THEN round(sum(debit),6)/sum(ingreso)    ELSE 0 END
					from get_kardex_v(20150101,20500101,'{0,""" +str(i.producto_rel.id)+ """}'::INT[], (select array_agg(id) from stock_location) ,"""+str(self.env.company.id)+""") 
					 
						left join stock_location origen on origen.id= get_kardex_v.ubicacion_origen
						left join stock_location destino on destino.id= get_kardex_v.ubicacion_destino
						where coalesce(origen.usage,'gasto_vinculado') <> 'internal' or coalesce(destino.usage,'gasto_vinculado') <> 'internal'
			""")
			rpta = 0
			for elem in self.env.cr.fetchall():
				rpta = elem[0]
			i.producto_rel.sudo().standard_price = rpta

		return t