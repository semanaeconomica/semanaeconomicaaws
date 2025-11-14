# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date

class StockPickingWizard(models.TransientModel):
	_name = 'stock.picking.wizard'

	name = fields.Char()
	guide_number = fields.Char(string='Numero de Guia para Anular')	
	cancel_reason = fields.Selection([('print_error','Error de Impresion'),
									('return','Devolucion')],string='Motivo de Anulacion')
	cancel_date = fields.Date(string=u'Fecha de Anulación',default=lambda self:date.today())

	def cancel_guide(self):
		picking = self.env['stock.picking'].browse(self.env.context['active_id'])
		
		self.env['stock.picking.anulation.line'].create({
														'picking_id':picking.id,
														'guide_number':self.guide_number,
														'cancel_reason':self.cancel_reason,
														'cancel_date':self.cancel_date,
														'res_user_id':self._uid
														})
		if picking.serie_guia and self.cancel_reason == 'print_error':
			picking.numberg = picking.serie_guia.next_by_id()
		wizard = self.env['stock.return.picking'].create({})
		if self.cancel_reason == 'return':
			picking.canceled_guide = True
			wizard._onchange_picking_id()
			context = self._context or {}
			return {
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.return.picking',
				'views':[[self.env.ref('stock.view_stock_return_picking_form').id,'form']],
				'target':'new',
				'context':context
			}
	

class StockReturnPicking(models.TransientModel):
	_inherit = 'stock.return.picking'

	def _create_returns(self):
		new_picking_id, picking_type_id = super(StockReturnPicking,self)._create_returns()
		new_picking = self.env['stock.picking'].search([('id', '=', new_picking_id)], limit=1)
		new_picking.canceled_guide = False
		new_picking.serie_guia = None
		new_picking.carrier_id_it = None
		new_picking.vehicle_id = None
		new_picking.driver_id = None
		new_picking.starting_point = None
		new_picking.ending_point = None
		new_picking.kardex_date = None
		#Falta Tipo Doc SUNAT 
		return new_picking_id, picking_type_id