# -*- coding: utf-8 -*-
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import time
import odoo.addons.decimal_precision as dp
from openerp.osv import osv
import base64
from odoo import models, fields, api
import codecs

values = {}

class tree_view_kardex_fisico(models.Model):
	_name = 'tree.view.kardex.fisico'
	_auto = False

	u_origen = fields.Char(string=u'Ubicación Origen')
	u_destino = fields.Char(string=u'Ubicación Destino')
	almacen = fields.Char(string=u'Almacén')
	t_opera = fields.Char(string=u'Tipo de Operación')
	categoria = fields.Char(string=u'Categoría')
	producto = fields.Char(string=u'Producto')
	cod_pro = fields.Char(string=u'Codigo P.')
	unidad = fields.Char(string=u'Unidad')
	fecha = fields.Char(string=u'Fecha')
	doc_almacen = fields.Char(string=u'Doc. Almacén')
	entrada = fields.Float(string=u'Entrada',digits=(12,2))
	salida = fields.Float(string=u'Salida',digits=(12,2))

class product_template(models.Model):
	_inherit = 'product.template'

	def get_kardex_fisico(self):
		products = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
		if len(products)>1:
			raise osv.except_osv('Alerta','Existen variantes de productos, debe sacarse el kardex desde variante de producto.')
		return {
			'context':{'active_id':products[0].id},
			'name': 'Kardex Fisico',
			'type': 'ir.actions.act_window',
			'res_model': 'make.kardex.product',
			'view_mode': 'form',
			'views': [(False, 'form')],
			'target': 'new',
		}

class product_product(models.Model):
	_inherit = 'product.product'

	def get_kardex_fisico(self):
		return {
			'context':{'active_id':self.id},
			'name': 'Kardex Fisico',
			'type': 'ir.actions.act_window',
			'res_model': 'make.kardex.product',
			'view_mode': 'form',
			'views': [(False, 'form')],
			'target': 'new',
		}

class make_kardex(models.TransientModel):
	_name = "make.kardex"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	products_ids=fields.Many2many('product.product','rel_wiz_kardex','product_id','kardex_id')
	location_ids=fields.Many2many('stock.location','rel_kardex_location','location_id','kardex_id','Ubicacion',required=True)
	allproducts=fields.Boolean('Todos los productos',default=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
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
		res = super(make_kardex, self).default_get(fields)
		import datetime
		fecha_hoy = str(datetime.datetime.now())[:10]
		fecha_inicial = fecha_hoy[:4] + '-01-01'
		res.update({'fecha_ini_mod':fecha_inicial})
		res.update({'fecha_fin_mod':fecha_hoy})
		res.update({'fini':fecha_inicial})
		res.update({'ffin':fecha_hoy})
		#locat_ids = self.pool.get('stock.location').search(cr, uid, [('usage','in',('internal','inventory','transit','procurement','production'))])
		locat_ids = self.env['stock.location'].search([('usage','in',('internal','internal'))])
		locat_ids = [elemt.id for elemt in locat_ids]
		res.update({'location_ids':[(6,0,locat_ids)]})
		return res

	@api.onchange('alllocations')
	def onchange_alllocations(self):
		if self.alllocations == True:
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]


class make_kardex_product(models.TransientModel):
	_name = "make.kardex.product"

	fini= fields.Date('Fecha inicial',required=True)
	ffin= fields.Date('Fecha final',required=True)
	location_ids=fields.Many2many('stock.location','rel_kardex_location_product','location_id','kardex_id','Ubicacion',required=True)
	destino = fields.Selection([('csv','CSV'),('crt','Pantalla')],'Destino')
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
		res = super(make_kardex_product, self).default_get(fields)
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
			locat_ids = self.env['stock.location'].search( [('usage','in',('internal','internal'))] )
			self.location_ids = [(6,0,locat_ids.ids)]
		else:
			self.location_ids = [(6,0,[])]



	def do_csvtoexcel(self):
		fields = {
			'fini':self.fini,
			'ffin':self.ffin,
			'products_ids':[(6,0,[self.env.context['active_id']])],
			'location_ids':[(6,0,self.location_ids)],
			'allproducts':self.allproducts,
			'destino':False,
			'check_fecha':self.check_fecha,
			'alllocations':self.alllocations,
			'fecha_ini_mod':self.fecha_ini_mod,
			'fecha_fin_mod':self.fecha_fin_mod,
			'analizador':self.analizador,
		}
		wizard_original = self.env['make.kardex'].create(fields)
		return wizard_original.do_csvtoexcel()