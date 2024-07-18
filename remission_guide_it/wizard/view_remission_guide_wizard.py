# -*- coding: utf-8 -*-
from odoo import fields,models,api, _
from odoo.exceptions import UserError
from datetime import *
import re,json,urllib3,base64

# Wizard para mostrar la preview de las guias de remision:
class Preview_Remission_Guide_Wizard(models.TransientModel):
	_name = 'preview.remission.guide.wizard'
	line_ids = fields.One2many('preview.remission.guide.wizard.line','wizard_id')
	
	picking_id = fields.Many2one('stock.picking')

	####COMPAÑIA####
	company_id = fields.Many2one(related='picking_id.company_id',string=u'Compañía')
	company_ruc = fields.Char(related='company_id.partner_id.vat')
	company_name = fields.Char(related='company_id.name')
	company_image = fields.Binary(related='company_id.logo')

	# picking fields:
	electronic_guide = fields.Boolean(related='picking_id.electronic_guide') 
	kardex_date = fields.Datetime(related='picking_id.kardex_date') 
	picking_type_id = fields.Many2one(related='picking_id.picking_type_id')
	name = fields.Char(related='picking_id.name')
	gross_weight = fields.Float(related='picking_id.total_gross_weight')
	num_pieces   = fields.Float(related='picking_id.number_of_packages')
	invoice_id = fields.Many2one(related='picking_id.invoice_id')
	transfer_reason_id = fields.Many2one(related='picking_id.reason_transfer')
	numberg = fields.Char(related='picking_id.numberg')
	note = fields.Text(related='picking_id.note')
	series  = fields.Char('Serie de Guia')
	number  = fields.Char('Nro de Guía')
	pdf_url = fields.Char(related='picking_id.print_web_version_pdf',string='PDF guía de remisión')
	success_message = fields.Char(string='*')
	
	receiver_partner_id = fields.Many2one('res.partner',related='picking_id.partner_id.commercial_partner_id')
	
	# Destinos:
	start_point   = fields.Char(string='Punto de Partida',related='picking_id.starting_point')
	ubigeo_start  = fields.Char(related='picking_id.picking_type_id.warehouse_id.partner_id.zip')
	point_arrival = fields.Char(string='Punto de llegada',related='picking_id.ending_point')
	ubigeo_arrival= fields.Char(related='picking_id.partner_id.zip')
	
	# transportista
	transporter_id = fields.Many2one(related='picking_id.carrier_id_it')
	transporter_doc_id = fields.Many2one(related='transporter_id.l10n_latam_identification_type_id')
	transporter_doc = fields.Char(related='transporter_id.vat')
	transporter_type = fields.Selection(related='picking_id.type_of_transport')

	# conductor
	driver_id = fields.Many2one(related='picking_id.driver_id',string='Conductor')
	driver_doc_id = fields.Many2one(related='driver_id.l10n_latam_identification_type_id')
	driver_doc    = fields.Char(related='driver_id.vat')
	
	license_num   = fields.Char(related='driver_id.number_driver_licence',string='Nro Licencia')

	vehicle_id = fields.Many2one(related='picking_id.vehicle_id')
	license_plate = fields.Char(related='vehicle_id.license_plate')
	
	date_traslate = fields.Date(related='picking_id.transfer_date',string='Fecha de traslado')

	def post_request(self):
		parameters = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		guide_line = next(filter(lambda s:s.series_id == self.picking_id.serie_guia,parameters.guide_series_ids))
		if not self.electronic_guide:
			return 
		series = self.env['remission.guide.series'].search([('series_id','=',self.picking_id.serie_guia.id),('parameter_id.company_id','=',self.company_id.id)],limit=1)
		# Validaciones:
		if not series:
			raise UserError(u'No se ha encontrado una configuración de parámetros para la serie de guía %s\nVaya a Contabilidad->Configuración->Parámetros->Guía de remisión Electrónica para configurarlos.'%self.picking_id.serie_guia.name)
		now = datetime.strftime(fields.Date.context_today(self),'%Y-%m-%d')
		date_traslate_pick = self.date_traslate if self.date_traslate else self.kardex_date.date()
		traslate = datetime.strftime(date_traslate_pick,'%Y-%m-%d')
		
		if not self.line_ids:
			raise UserError('No hay líneas de bienes disponibles')

		data = {
			"operacion": "generar_guia",
			"tipo_de_comprobante": 7, # guia de rem remitente = 7
			"serie": self.series,
			"numero": self.number,
			"cliente_tipo_de_documento": self.receiver_partner_id.l10n_latam_identification_type_id.code_sunat,
			"cliente_numero_de_documento":self.receiver_partner_id.vat,
			"cliente_denominacion": self.receiver_partner_id.name,
			"cliente_direccion": self.receiver_partner_id.street,
			"cliente_email": self.receiver_partner_id.email or '',
			"cliente_email_1": "",
			"cliente_email_2": "",
			"fecha_de_emision":now,
			"observaciones": 'LIC. ' + self.license_num + ' ' +self.note  if self.note else 'LIC. ' + self.license_num,
			"motivo_de_traslado": self.transfer_reason_id.code,
			"peso_bruto_total": str(self.gross_weight) if self.gross_weight else "0",
			"numero_de_bultos": str(self.num_pieces) if self.num_pieces else "0",
			"tipo_de_transporte": self.transporter_type,
			"fecha_de_inicio_de_traslado": traslate,
			"transportista_documento_tipo": self.transporter_doc_id.code_sunat,
			"transportista_documento_numero": self.transporter_doc,
			"transportista_denominacion": self.transporter_id.name,
			"transportista_placa_numero": self.license_plate or "",
			"conductor_documento_tipo": self.driver_doc_id.code_sunat,
			"conductor_documento_numero": self.driver_doc,
			"conductor_denominacion": self.driver_id.name,
			"punto_de_partida_ubigeo": self.ubigeo_start if self.ubigeo_start else self.picking_id.picking_type_id.warehouse_id.partner_id.district_id.code,
			"punto_de_partida_direccion": self.start_point,
			"punto_de_llegada_ubigeo": self.ubigeo_arrival if self.ubigeo_arrival else self.picking_id.partner_id.district_id.code,
			"punto_de_llegada_direccion": self.point_arrival,
			"enviar_automaticamente_a_la_sunat": "true",
			"enviar_automaticamente_al_cliente": "true",
			"codigo_unico": "",
			"formato_de_pdf": "",
			"items": [{
				"unidad_de_medida":'ZZ' if l.product_id.type=='service' else 'NIU',
				"codigo": l.default_code,
				"descripcion": l.product_id.name,
				"cantidad": l.quantity,
			} for l in self.line_ids]
		}
		self.picking_id.json_post = data
		http = urllib3.PoolManager()
		try:
			r = http.request('POST',
							guide_line.path,
							headers = {'Content-Type':'application/json',
									   'Authorization':'Token token = "%s"'%guide_line.token},
							body = json.dumps(data))
		except urllib3.exceptions.HTTPError as e:
			raise UserError(u'Error al procesar datos de guía electrónica!\nDetalles:\n'+e.read())
		response = json.loads(r.data.decode('utf-8'))
		self.picking_id.json_get = response
		if 'errors' in response:
			raise UserError('Respuesta del Facturador: ' + response['errors'])
		if 'enlace_del_pdf' in response:
			self.picking_id.print_web_version_pdf = response['enlace_del_pdf']
		if 'enlace_del_xml' in response:
			self.picking_id.print_web_version_xml = response['enlace_del_xml']
		if 'aceptada_por_sunat' in response:
			self.picking_id.sunat_state = '3'
			self.success_message = u'La transacción se realizó con éxito!'

		return {"type": "ir.actions.do_nothing",}

	def print_remission_guide(self):
		# Ya que cada empresa/cliente tiene un formato particular de guía de remisión,
		# el método print_remision de stock.picking debe encargarse de eso.
		method = getattr(self.picking_id,'print_remision',None)
		if callable(method):
			return self.picking_id.print_remision()
		return True

	def download_pdf_file(self):
		if not self.electronic_guide or not self.pdf_url:
			raise UserError('Archivo PDF no disponible')
		try:
			if self.pdf_url != '':
				http = urllib3.PoolManager()
				response = http.request('GET',self.pdf_url)
			else:
				return
		except urllib3.exceptions.HTTPError as err:
			if err.code == 404:
				raise UserError(u'El archivo ha sido removido o no está disponible')
			else:
				raise UserError(u'Ha ocurrido un error al intentar obtener su archivo.')
		else:
			return self.env['popup.it'].get_file(u'Guia Electrónica %s.pdf'%self.numberg,base64.encodestring(response.data))
		
		
class PreviewRemissionGuideWizardLine(models.TransientModel):
	_name = 'preview.remission.guide.wizard.line'
	wizard_id = fields.Many2one('preview.remission.guide.wizard')
	move_id   = fields.Many2one('stock.move')
	product_id = fields.Many2one(related='move_id.product_id')
	quantity = fields.Float(related='move_id.product_uom_qty')
	uom_id   = fields.Many2one(related='move_id.product_uom')
	default_code = fields.Char(related='product_id.default_code')


