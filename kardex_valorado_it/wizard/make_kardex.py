# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs
from datetime import timedelta

values = {}

class account_move(models.Model):
	_inherit = 'account.move'

	check_use_date_kardex = fields.Boolean('Establecer fecha en Kardex',default=False)
	date_kardex = fields.Datetime('Fecha Kardex')

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	check_gastos_vinculados = fields.Boolean('Gastos Vinculados con Fecha Kardex del Albaran?',default=False)
	anular_albaranres_view = fields.Boolean('Automaticamente no visualizar albaranes de Anulacion de Guia',default=False)

class stock_picking(models.Model):
	_inherit = 'stock.picking'

	tc = fields.Float('Tipo Cambio',digits=(12,3),default=1)

	def write(selfs,vals):
		t = super(stock_picking,selfs).write(vals)    
		for self in selfs:
			if 'nomore' in self.env.context:
				pass
			else:
				fecha_pedido = False
				moneda = False
				import datetime
				for i in self.move_ids_without_package:
					if i.purchase_line_id.id and i.purchase_line_id.order_id.id and i.purchase_line_id.order_id.date_approve:
						fecha_pedido = (self.kardex_date if self.kardex_date else datetime.datetime.now()) - timedelta(hours=5)
						moneda = i.purchase_line_id.order_id.currency_id.name
				if self.state == 'done' and fecha_pedido and moneda == 'USD' and self.tc == 1:
					if self.location_dest_id.usage == 'internal' and self.location_id.usage == 'internal':
						pass
					else:
						tp = self.env['res.currency.rate'].search([('currency_id.name','=','USD'),('name','=', fecha_pedido )])
						if len(tp)==0 and not self.invoice_id.id:
							raise osv.except_osv('Alerta','No existen el tipo de cambio para ' + fecha_pedido.strftime("%Y-%m-%d") + ' del pedido de compra en dolares del albaran ' + self.name)						
						if len(tp)==0 and self.invoice_id.id:
							raise osv.except_osv('Alerta','No existen el tipo de cambio para ' + self.invoice_id.invoice_date.strftime("%Y-%m-%d") + ' de la facura en dolares del albaran ' + self.name)						
						self.with_context({'nomore':1}).write({'tc':tp[0].sale_type})
		return t


class stock_move(models.Model):
	_inherit = 'stock.move'

	price_unit_it = fields.Float('Precio Unitario',digits=(12,8))
	price_unit_it_dolar = fields.Float('Precio Unitario',digits=(12,8))

	def write(selfs,vals):
		t = super(stock_move,selfs).write(vals)
		for self in selfs:
			if 'nomore' in self.env.context:
				pass
			else:
				if self.purchase_line_id.id and 'price_unit_it' not in vals and not self.origin_returned_move_id.id:
					elem  = self.purchase_line_id.price_subtotal / self.purchase_line_id.product_qty if self.purchase_line_id.product_qty != 0 else 0
					elem = elem*self.purchase_line_id.product_uom.factor
					elem = elem*self.product_uom.factor_inv
					self.with_context({'nomore':1}).write({'price_unit_it':elem,'price_unit_it_dolar':elem})
				elif self.origin_returned_move_id.id and 'price_unit_it' not in vals:					
					self.with_context({'nomore':1}).write({'price_unit_it':self.origin_returned_move_id.price_unit_it,'price_unit_it_dolar':self.origin_returned_move_id.price_unit_it_dolar})
		return t

	def actualizar_priceunit(self):
		return {
			'context': {'form_view_initial_mode':'edit'},
			'name': 'Precio Unitario',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.move',
			'view_mode': 'form',
			'target': 'new',
			'res_id': self.id,
			'views': [(self.env.ref('kardex_valorado_it.stockmove_editpriceunit').id, 'form')],
		}


class make_kardex_valorado(models.TransientModel):
	_name = "make.kardex.valorado"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex_valorado','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location_valorado','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV')],'Destino')
	check_fecha = fields.Boolean('Editar Fecha')
	alllocations = fields.Boolean('Todos los almacenes',default=True)

	fecha_ini_mod = fields.Date('Fecha Inicial')
	fecha_fin_mod = fields.Date('Fecha Final')
	analizador = fields.Boolean('Analizador')

	@api.onchange('fecha_ini_mod')
	def onchange_fecha_ini_mod(self):
		self.fini = self.fecha_ini_mod


	@api.onchange('fecha_fin_mod')
	def onchange_fecha_fin_mod(self):
		self.ffin = self.fecha_fin_mod


	@api.model
	def default_get(self, fields):
		res = super(make_kardex_valorado, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})

		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','inventory','transit','procurement','production'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]



class make_kardex_product(models.TransientModel):
	_inherit = "make.kardex.product"



	def do_csvtoexcel(self):
		fields = {
			'fini':self.fini,
			'ffin':self.ffin,
			'products_ids':[(6,0,[self.env.context['active_id']])],
			'location_ids':[(6,0,self.location_ids.ids)],
			'allproducts':False,
			'destino':False,
			'check_fecha':self.check_fecha,
			'alllocations':self.alllocations,
			'fecha_ini_mod':self.fecha_ini_mod,
			'fecha_fin_mod':self.fecha_fin_mod,
			'analizador':self.analizador,
		}
		wizard_original = self.env['make.kardex.valorado'].create(fields)
		return wizard_original.with_context({'res_model_it':'make.kardex.product','id_it':self.id}).do_csvtoexcel()


class LandedCostItLine(models.Model):
	_inherit = 'landed.cost.it.line'

	precio_unitario_rel = fields.Float(string='Precio Unitario', compute="get_price_unit_it")

	def get_price_unit_it(self):
		for i in self:
			i.precio_unitario_rel = i.stock_move_id.price_unit_it * i.stock_move_id.picking_id.tc
