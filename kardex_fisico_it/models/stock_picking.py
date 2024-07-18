# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time
from odoo import api, fields, models, _ , exceptions

from openerp.osv import osv

class type_operation_kardex(models.Model):
	_name = 'type.operation.kardex'

	name = fields.Char('Nombre')
	code = fields.Char('Codigo')


class stock_move_line(models.Model):
	_inherit = 'stock.move.line'

	kardex_date = fields.Datetime(string='Fecha kardex', readonly=False,copy=False,track_visibility='always',compute="get_kardex_date",inverse="set_kardex_date")
	no_mostrar = fields.Boolean('No mostrar en kardex',compute="get_no_mostrar",inverse="set_no_mostrar")

	def get_kardex_date(self):
		for i in self:
			i.kardex_date = i.move_id.kardex_date

	def get_no_mostrar(self):
		for i in self:
			i.no_mostrar = i.move_id.no_mostrar

	def set_kardex_date(self):
		for i in self:
			i.move_id.kardex_date = i.kardex_date

	def set_no_mostrar(self):
		for i in self:
			i.move_id.no_mostrar = i.no_mostrar

class stock_move(models.Model):
	_inherit = 'stock.move'

	invoice_id = fields.Many2one('account.move','Factura',domain=[('type', 'in', ['out_invoice','in_invoice','out_refund','in_refund'])])

	kardex_date = fields.Datetime(string='Fecha kardex', readonly=False,copy=False,track_visibility='always')
	no_mostrar = fields.Boolean('No mostrar en kardex')	

	def _action_confirm(self, merge=True, merge_into=False):
		t = super(stock_move,self)._action_confirm(False,merge_into)
		return t

	def write(self,vals):
		t = super(stock_move,self).write(vals)
		if 'no_mostrar' in vals and 'permitido' in self.env.context:
			pass
		else:
			if 'no_mostrar' in vals and 'permitido' not in self.env.context:
				permiso = self.env['res.groups'].search([('name','=','Permitir Editar: No mostrar Kardex')])
				if len(permiso)>0:
					if self.env.uid in permiso[0].users.ids:
						pass
					else:
						raise osv.except_osv('Alerta','No tiene permisos de No Mostrar Kardex (Detalle)' + str(self.env.context) )


		if 'kardex_date' in vals and 'permitido' in self.env.context:
			pass
		elif 'kardex_date' in vals and 'permitido' not in self.env.context:
			permiso = self.env['res.groups'].search([('name','=','Permitir Editar Fecha Kardex')])
			if len(permiso)>0:
				if self.env.uid in permiso[0].users.ids:
					pass
				else:
					raise osv.except_osv('Alerta','No tiene permisos de Edicion del Kardex')
		return t


class PickingType(models.Model):
	_inherit = "stock.picking"


	kardex_date = fields.Datetime(string='Fecha kardex', readonly=False,copy=False,track_visibility='always')
	no_mostrar = fields.Boolean('No mostrar en kardex',default=False)
	use_kardex_date = fields.Boolean('Usar Fecha kardex',default=True)
	invoice_id = fields.Many2one('account.move','Factura',domain=[('type', 'in', ['out_invoice','in_invoice','out_refund','in_refund'])])
	type_operation_sunat_id = fields.Many2one('type.operation.kardex','Tipo de Operacion SUNAT')
	

	@api.onchange('no_mostrar')
	def onchange_no_mostrar(self):
		for i in self:		
			for line in i.move_ids_without_package:
				line.with_context({'permitido':1}).no_mostrar = i.no_mostrar

	@api.onchange('invoice_id')
	def onchange_invoice_id(self):
		for i in self:
			if i.invoice_id.id:
				for line in i.move_ids_without_package:
					line.invoice_id = i.invoice_id.id

	def action_done(self):
		t = super(PickingType,self).action_done()
		if not self.kardex_date:
			self.with_context({'permitido':1}).write({'kardex_date': fields.Datetime.now()})
			for i in self:
				i.move_ids_without_package.with_context({'permitido':1}).write({'kardex_date': fields.Datetime.now()})
		else:
			for i in self:
				i.move_ids_without_package.with_context({'permitido':1}).write({'kardex_date': i.kardex_date})

		return t

	def write(self,vals):
		t = super(PickingType,self).write(vals)
		if 'invoice_id' in vals:
			for i in self:
				i.move_ids_without_package.with_context({'permitido':1}).write({'invoice_id': vals['invoice_id'] })
				
		if 'no_mostrar' in vals and 'permitido' not in self.env.context:
			permiso = self.env['res.groups'].search([('name','=','Permitir Editar: No mostrar Kardex')])
			if len(permiso)>0:
				if self.env.uid in permiso[0].users.ids:
					for i in self:
						i.move_ids_without_package.with_context({'permitido':1}).write({'no_mostrar': vals['no_mostrar'] })					
				else:
					raise osv.except_osv('Alerta','No tiene permisos de No Mostrar Kardex (Cabecera)')

		if 'kardex_date' in vals and 'permitido' in self.env.context:
			pass
		elif 'kardex_date' in vals and 'permitido' not in self.env.context:
			permiso = self.env['res.groups'].search([('name','=','Permitir Editar Fecha Kardex')])
			if len(permiso)>0:
				if self.env.uid in permiso[0].users.ids:
					for i in self:
						i.move_ids_without_package.with_context({'permitido':1}).write({'kardex_date': vals['kardex_date'] })
				else:
					raise osv.except_osv('Alerta','No tiene permisos de Edicion del Kardex')
		return t