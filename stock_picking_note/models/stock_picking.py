# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date,datetime
from odoo.exceptions import UserError
import base64
import re

from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	campo_temp = fields.Boolean(string='tipo de picking', compute='calculate_tipo_pinking', store=False)
	numberg = fields.Char(string=u'Serie de guía')
	client_order_ref = fields.Char(u'Orden de Compra Cliente')
	serie_guia = fields.Many2one('ir.sequence', string=u'Serie de guia',domain="[('company_id', '=', company_id)]")
	is_manager = fields.Boolean(string='manager', compute='check_in_group', store=False)

	###TRANSPORTE
	carrier_id_it = fields.Many2one('res.partner',string='Transportista',domain=[('is_company', '=', True)])
	vehicle_id = fields.Many2one('fleet.vehicle',string=u'Vehículo')
	driver_id = fields.Many2one('res.partner', string='Conductor',domain=[('is_company', '=', False)])
	starting_point = fields.Char(string=u'Punto de Partida')
	ending_point = fields.Char(string=u'Punto de Llegada')
	reason_transfer = fields.Many2one('einvoice.catalog.20',string=u'Motivo de Traslado')
	transfer_date = fields.Date(string='Fecha de Traslado')
	type_of_transport = fields.Selection([('01',u'TRANSPORTE PÚBLICO'),('02',u'TRANSPORTE PRIVADO')],string='Tipo de Transporte')

	###ANULACION DE GUIAS
	canceled_guide = fields.Boolean(string='Guia Anulada',default=False)
	related_location = fields.Selection(string='Related Location',related='location_id.usage',store=True)
	related_location_dest = fields.Selection(string='Related Location Dest',related='location_dest_id.usage',store=True)
	anulation_line_ids = fields.One2many('stock.picking.anulation.line','picking_id')
	can_anulated = fields.Boolean(string='anulador', compute='check_in_group_anulated', store=False)

	@api.onchange('vehicle_id')
	def _onchange_vehicle(self):
		for i in self:
			if i.vehicle_id:
				i.driver_id = i.vehicle_id.driver_id.id

	@api.onchange('picking_type_id')
	def _onchange_picking_type_id(self):
		for i in self:
			if i.picking_type_id.warehouse_id.partner_id.street:
				i.starting_point = i.picking_type_id.warehouse_id.partner_id.street

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		for i in self:
			if i.partner_id.street:
				i.ending_point = i.partner_id.street

	@api.depends('can_anulated')
	def check_in_group_anulated(self):
		in_group = False
		usuario = self.env.uid
		grupo = self.env['res.groups'].search([('name','=','Anular Guias Remision')]).id
		self.env.cr.execute("""
			select *
			from res_groups_users_rel
			where gid = """+str(grupo)+""" and uid = """+str(usuario))
		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			in_group = True
		self.can_anulated = in_group

	@api.depends('is_manager')
	def check_in_group(self):
		in_group = False
		usuario = self.env.uid
		grupo = self.env['res.groups'].search([('name','=','Guias Manager')]).id
		self.env.cr.execute("""
			select *
			from res_groups_users_rel
			where gid = """+str(grupo)+""" and uid = """+str(usuario))
		res = self.env.cr.dictfetchall()
		if len(res) > 0:
			in_group = True
		self.is_manager = in_group

	@api.depends('campo_temp', 'numberg')
	def calculate_tipo_pinking(self):
		no_hide = False
		if self.picking_type_id:
			if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
				no_hide = True

		self.campo_temp = no_hide

	def get_wizard(self):
		wizard = self.env['stock.picking.wizard'].create({'name':'Cancelar Guia','guide_number':self.numberg})
		if (self.related_location == 'internal' and self.related_location_dest == 'internal') or (self.related_location == 'internal' and self.related_location_dest == 'customer'):
			return {
				'type':'ir.actions.act_window',
				'res_id':wizard.id,
				'view_type':'form',
				'view_mode':'form',
				'res_model':'stock.picking.wizard',
				'views':[[self.env.ref('stock_picking_note.stock_view_picking_form_wizard').id,'form']],
				'target':'new',
			}

	@api.onchange('serie_guia')
	def changed_serie_guia(self):
		if self.serie_guia:
			self.refres_numg()

	@api.model
	def create(self, vals):
		if 'picking_type_id' in vals:
			pt = self.env['stock.picking.type'].search([('id', '=', vals['picking_type_id'])])
			if pt.code == 'internal' or pt.code == 'outgoing':
				if 'serie_guia' in vals:
					res = ''
					serie_guia = self.env['ir.sequence'].browse(vals['serie_guia'])
					if serie_guia.prefix:
						res = serie_guia.prefix
					number = str(serie_guia.number_next_actual)
					if serie_guia.padding:
						number = number.rjust(serie_guia.padding, '0')
					res = res + number
					vals['numberg'] = res
				if pt.serie_guia:
					res = ''
					if pt.serie_guia.prefix:
						res = pt.serie_guia.prefix
					number = str(pt.serie_guia.number_next_actual)
					if pt.serie_guia.padding:
						number = number.rjust(pt.serie_guia.padding, '0')

					res = res + number
					vals['numberg'] = res
					vals['serie_guia'] = pt.serie_guia.id
			else:
				vals['numberg'] = False
			if pt.warehouse_id.partner_id.street:
				vals['starting_point'] = pt.warehouse_id.partner_id.street
		if 'partner_id' in vals:
			rp = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
			if rp.street:
				vals['ending_point'] = rp.street
		return super(StockPicking,self).create(vals)

	def write(self, vals):
		if 'picking_type_id' in vals:
			pt = self.env['stock.picking.type'].search([('id', '=', vals['picking_type_id'])])
			if pt.code == 'internal' or pt.code == 'outgoing':
				if 'serie_guia' in vals:
					serie_guia_id = vals['serie_guia']
				else:
					serie_guia_id = self.serie_guia
				serie_guia = self.env['ir.sequence'].browse(serie_guia_id)

				if serie_guia:
					if 'numberg' in vals:
						res = self.makecurrentsequecenumber(serie_guia)
						vals['numberg'] = res
			else:
				vals['numberg'] = False

		ctx = dict(self._context or {})
		return super(StockPicking,self.with_context(ctx)).write(vals)

	def makecurrentsequecenumber(self, sequence_act):
		res = ''
		if sequence_act.prefix:
			res = sequence_act.prefix
		number = str(sequence_act.number_next_actual)
		if sequence_act.padding:
			number = number.rjust(sequence_act.padding, '0')
		res = res + number
		return res

	@api.depends('numberg')
	def refres_numg(self):
		if self.state == 'done':
			return
		self.numberg = False
		if self.state not in ['done', 'cancel']:
			if self.picking_type_id.code in ['internal','outgoing']:
				if self.serie_guia:
					res = self.makecurrentsequecenumber(self.serie_guia)
					self.numberg = res

	@api.depends('numberg')
	@api.onchange('picking_type_id')
	def change_picking_type(self):
		self.numberg = False
		if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
			if self.picking_type_id.serie_guia:
				if not self.serie_guia:
					self.serie_guia = self.picking_type_id.serie_guia
					res = self.makecurrentsequecenumber(self.serie_guia)
					self.numberg = res

	def button_validate(self):
		self.validate_limit_line()
		parameters = self.env['main.parameter.warehouse'].search([], limit=1)
		if str(self.kardex_date) != str(date.today()) and not 'a' in self.env.context and parameters.date_albaran_validate:
			view = self.env.ref('stock_picking_note.view_confirm_date_picking_form')
			wiz = self.env['confirm.date.picking'].create({'pick_id': self.id})
			return {
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'confirm.date.picking',
				'views': [(view.id, 'form')],
				'view_id': view.id,
				'target': 'new',
				'res_id': wiz.id,
				'context': self.env.context,
			}
		else:
			self.update_serie_next_guia()
		return super(StockPicking,self).button_validate()

	def update_serie_next_guia(self):
		if self.picking_type_id.code == 'internal' or self.picking_type_id.code == 'outgoing':
			if self.serie_guia:
				print(self.numberg)
				self.numberg = self.serie_guia._next()

	def validate_limit_line(self):
		parameters  = self.env['main.parameter.warehouse'].search([],limit=1)
		if self.picking_type_code != 'outgoing' or not parameters.albaran_limit_line:
			return
		limit_lines = parameters.albaran_limit_line
		lines_operation = self.env['stock.move.line'].search([('picking_id','=',self.id),('qty_done','>',0)])
		lines_operation_to_zero = self.env['stock.move.line'].search([('picking_id','=',self.id),('qty_done','=',0)])
		lines_view = len(self.move_line_ids_without_package)
		if len(lines_operation)>limit_lines or (len(lines_operation_to_zero)==lines_view and lines_view > limit_lines):
			raise UserError(u'La cantidad de items del albarán supera el limite ('+str(limit_lines)+') permitido para la Guía de Remisión.')

	def print_remision(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).dir_create_file
		name_file = 'Guia_Remision.pdf'
		doc = SimpleDocTemplate(direccion + name_file ,pagesize=letter, rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)
		elements = []

		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9, fontName="Helvetica")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9, fontName="Helvetica")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9, fontName="Helvetica")

		if self.kardex_date:
			kardex_date = self.kardex_date
		elif self.date_done:
			kardex_date = self.date_done
		else:
			kardex_date = self.scheduled_date

		spacer = Spacer(50, 100)
		elements.append(spacer)
		elements.append(Paragraph('%s' % (self.numberg if self.numberg else ''), style_left))

		datos_fecha = []
		datos_fecha.append([Paragraph(kardex_date.strftime('%d'),style_cell),Paragraph(kardex_date.strftime('%B'),style_cell),Paragraph(kardex_date.strftime('%Y'),style_cell)])
		table_datos_fecha = Table(datos_fecha, colWidths=[3*cm,3*cm,3*cm], hAlign='LEFT')
		elements.append(table_datos_fecha)

		datos_partner = []
		datos_partner.append([Paragraph(self.partner_id.commercial_partner_id.name if self.partner_id else '',style_left),
							Paragraph(self.partner_id.commercial_partner_id.vat if self.partner_id.commercial_partner_id.vat else '',style_right)])
		table_datos_partner = Table(datos_partner, colWidths=[15.5*cm,4*cm])
		elements.append(table_datos_partner)

		elements.append(Paragraph('%s' % self.origin if self.origin else '', style_right))

		datos_transporte = []
		datos_transporte.append([Paragraph('',style_left),
							Paragraph(self.carrier_id_it.name if self.carrier_id_it else '',style_left),
							Paragraph('',style_left),
							Paragraph(self.reason_transfer.name if self.reason_transfer else '',style_left,)])
		datos_transporte.append([Paragraph('',style_left),
							Paragraph(self.vehicle_id.name if self.vehicle_id else '',style_left),
							Paragraph('',style_left),
							Paragraph(self.starting_point if self.starting_point else '',style_left,)])
		datos_transporte.append([Paragraph('',style_left),
							Paragraph(self.driver_id.name if self.driver_id else '',style_left),
							Paragraph('',style_left),
							Paragraph(self.ending_point if self.ending_point else '',style_left,)])
		table_datos_transporte = Table(datos_transporte, colWidths=[2*cm,6*cm,2*cm,6*cm])
		elements.append(table_datos_transporte)

		elements.append(Spacer(5, 10))
		datos = []
		x=0
		for fila in self.move_line_ids_without_package:
			datos.append([])
			datos[x].append(Paragraph((fila.product_id.default_code) if fila.product_id.default_code else '',style_cell))
			datos[x].append(Paragraph(str(fila.qty_done) if fila.qty_done else '0.00',style_cell))
			datos[x].append(Paragraph((fila.product_uom_id.name) if fila.product_uom_id else '',style_cell))
			datos[x].append(Paragraph((fila.product_id.name) if fila.product_id.name else '',style_left))
			x+=1

		table_datos = Table(datos, colWidths=[3.5*cm,2*cm,2*cm,15*cm])
		elements.append(table_datos)
		elements.append(spacer)
		elements.append(Paragraph('%s' % self.picking_type_id.company_id.partner_id.vat if self.picking_type_id.company_id.partner_id.vat else '', style_left))
		doc.build(elements)

		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(name_file,base64.encodestring(b''.join(f.readlines())))

class StockPickingAnulationLine(models.Model):
	_name = 'stock.picking.anulation.line'

	picking_id = fields.Many2one('stock.picking')
	guide_number = fields.Char(string='Numero de Guia')
	cancel_reason = fields.Selection([('print_error','Error de Impresion'),
									('return','Devolucion')],string='Motivo de Anulacion')
	cancel_date = fields.Date(string='Fecha de Anulacion')
	res_user_id = fields.Many2one('res.users',string='Usuario')
