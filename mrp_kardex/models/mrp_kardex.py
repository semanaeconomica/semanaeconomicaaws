# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import *
from datetime import timedelta


class sql_kardex(models.Model):
	_inherit ='sql.kardex'

	def _have_mrp(self):
		return True

class stock_move_line(models.Model):
	_inherit = 'stock.move.line'

	def edit_kardex_date(self):
		return {			
			'name':u'Editar Fecha Kardex',
			'res_id':self.id,
			'view_mode': 'form',
			'res_model': 'stock.move.line',
			'view_id': self.env.ref("mrp_kardex.move_line_fecha_kardex").id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}


	def edit_mostrar_no(self):
		return {			
			'name':u'Editar No Mostrar en Kardex',
			'res_id':self.id,
			'view_mode': 'form',
			'res_model': 'stock.move.line',
			'view_id': self.env.ref("mrp_kardex.move_line_no_mostrar").id,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}


class MrpProduction(models.Model):
	_inherit = 'mrp.production'

	kardex_date = fields.Date(string="Fecha Kardex", default=lambda self: date.today() - timedelta(hours=5))
	no_mostrar = fields.Boolean('No Mostrar en Kardex')
	operation_type_sunat_consume = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Consumo")
	operation_type_sunat_fp = fields.Many2one('type.operation.kardex', string="Tipo de Operacion Sunat Producto Terminado")

	def write(self,vals):
		t = super(MrpProduction,self).write(vals)
		if 'no_mostrar' in vals:
			for i in self:
				move_line_ids = self.env['stock.move.line'].search(['|', ('move_id.raw_material_production_id', '=', i.id), ('move_id.production_id', '=', i.id)])
				move_line_ids.with_context({'permitido':1}).write({'no_mostrar':vals['no_mostrar']})
		if 'kardex_date' in vals:
			for i in self:
				move_line_ids = self.env['stock.move.line'].search(['|', ('move_id.raw_material_production_id', '=', i.id), ('move_id.production_id', '=', i.id)])
				move_line_ids.with_context({'permitido':1}).write({'kardex_date':vals['kardex_date']})
				move_line_ids.refresh()
				for elem in move_line_ids:
					elem.refresh()
					elem.with_context({'permitido':1}).write({'kardex_date':elem.kardex_date + timedelta(hours=5)})
					
		return t


	def button_mark_done(self):
		self.ensure_one()
		error = ''
		self.with_context({'permitido':1}).write({'kardex_date':self.kardex_date,'no_mostrar':self.no_mostrar})
		for line in self.move_raw_ids:
			if line.quantity_done == 0:
				error += '- %s.\n' % (line.product_id.name)
		if error:
			raise UserError('Las cantidades consumidas no pueden quedar en cero en los siguientes productos:\n %s' % (error))
		return super(MrpProduction, self).button_mark_done()