# -*- encoding: utf-8 -*-
from openerp.osv import osv
import base64
from openerp import models, fields, api , exceptions, _
import csv
from tempfile import TemporaryFile
from odoo.exceptions import UserError

class import_rest_inv1(models.Model):
	_name = 'import.rest.inv1'

	@api.depends('picking_type_id','date_inv')
	def _get_name(self):
		for i in self:
			i.name = i.picking_type_id.name +' '+ i.date_inv.strftime('%d/%m/%Y')
			
	name = fields.Char(compute=_get_name,store=True)
	file_inv = fields.Binary('Archivo con saldos', required=True)
	location_id = fields.Many2one('stock.location', u'Almacén Origen', required=True)
	location_dest_id = fields.Many2one('stock.location', u'Almacén Destino', required=True)
	date_inv = fields.Date('Fecha del inventario', required=True)
	picking_type_id = fields.Many2one('stock.picking.type', 'Tipo de Picking', required=True)
	lines = fields.One2many('import.rest.inv.deta1','import_id','Detalle a Importar')
	limit = fields.Integer('Limite', required=True)
	mistakes = fields.Binary('Lineas no importadas')
	separator = fields.Char('Separador', required=True)
	operation_type = fields.Many2one('type.operation.kardex', 'Tipo de Operacion SUNAT', required=True)
	check_company = fields.Boolean(string=u'Identificar Producto por Compañía',help=u'Si esta marcado el importador de saldos identificara los productos por Compañía, de lo contrario no se aplicará dicho filtro',default=False)
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	@api.onchange('picking_type_id')
	def get_default_locations(self):
		for record in self:
			self.location_id = record.picking_type_id.default_location_src_id.id or None
			self.location_dest_id = record.picking_type_id.default_location_dest_id or None

	def verify_columns(self, route, columns):
		log = ''
		process_file = open(route, 'r')
		for c, i in enumerate(process_file, 1):
			i = i.split(self.separator)
			if len(i) != columns:
				log += 'Linea ' + str(c) + '\n'
		process_file.close()
		if log:
			raise UserError('El archivo debe contener ' + columns + ' columnas en cada fila, las siguientes lineas no cumplen esta condicion: \n' + log)
	
	def load_lines(self):
		self.ensure_one()
		self.lines.unlink()
		if self.file_inv:
			self.env.cr.execute("set client_encoding ='UTF8';")
			line_obj = self.env['import.rest.inv.deta1']
			MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
			if not MainParameter.dir_create_file:
				raise UserError('No se ha configurado una ruta de descarga dentro de Parametros Principales de Contabilidad')
			route = MainParameter.dir_create_file + 'initial_balance.csv'
			tmp = open(route, 'wb+')
			tmp.write(base64.b64decode(self.file_inv))
			tmp.close()
			self.verify_columns(route, 3)

			#Creación de líneas en pantalla.
			flag, errors = False, []
			process_file = open(route, 'r')
			for data in process_file:
				data = data.split(self.separator)
				try:
					pro = self.find_product_product(data[0])
					tmpl = self.env['product.template'].browse(pro.product_tmpl_id.id)
					if pro:
						vals = {
							'product_id': pro.id,
							'product_qty': float(data[1]),
							'price_unit': float(data[2]),
							'import_id': self.id,
						}
						line_obj.create(vals)
					else:
						flag = True
						errors.append("%s|%s|%s\n" % (data[0], data[1], data[2]))
				except Exception as e:
					raise UserError(e)
			process_file.close()
			if flag:
				with open(MainParameter.dir_create_file + "lineas_no_importadas.csv", "w") as f:
					for e in errors:
						print(e, file=f)
				f = open(MainParameter.dir_create_file + "lineas_no_importadas.csv", "rb")
				self.mistakes = base64.encodestring(b''.join(f.readlines()))

	def find_product_product(self,code):
		product_obj = self.env['product.product']
		filtro = [('default_code', '=', code)]
		if self.check_company:
			filtro.append(('company_id','=',self.company_id.id))
		pro = product_obj.search(filtro, limit=1)
		return pro

	def create_inv(self):
		self.ensure_one()
		npicking, array_pickings = 0, [] 
		if not self.location_dest_id.name:
			raise UserError("El almacen de destino seleccionado no tiene ubicacion padre")
		vals_picking = {
			'partner_id': self.env.company.partner_id.id,
			'location_id': self.location_id.id,
			'location_dest_id': self.location_dest_id.id,
			'kardex_date': self.date_inv,
			'origin': 'Inventario Inicial',
			'date_done': self.date_inv,
			'picking_type_id': self.picking_type_id.id,
			'date': self.date_inv,
			'name': 'Inventario - %d - %s - %d' % (npicking, self.location_dest_id.name, self.id),
			'type_operation_sunat_id': self.operation_type.id,
			'company_id':self.company_id.id,
		}
		picking = self.env['stock.picking'].with_context(mail_create_nosubscribe=True).create(vals_picking)
		array_pickings.append(picking)
		count = 1
		for line in self.lines:
			move = self.env['stock.move'].with_context(mail_create_nosubscribe=True).create(self._get_move_values(line.product_id, line.price_unit, line.product_qty,
																	   self.location_id.id, self.location_dest_id.id, picking))
			count = count + 1
			if count > self.limit:
				npicking = npicking + 1
				vals_picking.update({'name': 'Inventario - %d - %s - %d' % (npicking, self.location_dest_id.name, self.id)})
				picking = self.env['stock.picking'].with_context(mail_create_nosubscribe=True).create(vals_picking)
				array_pickings.append(picking)
				count = 1

		return self.env['popup.it'].get_message('Importacion Exitosa')

	def _get_move_values(self, product, price_unit, qty, location_id, location_dest_id, idmain):
		return {
			'product_id': product.id,
			'product_uom': product.uom_id.id,
			'product_uom_qty': qty,
			'price_unit_it': price_unit,
			'date': self.date_inv,
			'location_id': location_id,
			'location_dest_id': location_dest_id,
			'picking_id': idmain.id,
			'origin': 'Inventario Inicial',
			'picking_type_id': self.picking_type_id.id,
			'date_expected': self.date_inv,
			'name': _('INV:') + (idmain.name or ''),
			'company_id':self.company_id.id,
		}
				
class import_rest_inv_deta1(models.Model):
	_name = 'import.rest.inv.deta1'

	product_id = fields.Many2one('product.product','Producto')
	product_qty = fields.Float('Cantidad',digits=(20,6))
	price_unit = fields.Float('Precio',digits=(20,6))
	import_id = fields.Many2one('import.rest.inv1','Cabecera importador')