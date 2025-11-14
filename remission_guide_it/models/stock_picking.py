# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import re

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	electronic_guide = fields.Boolean(string=u'Es Guía Electrónica',default=False,copy=False)
	sunat_state = fields.Selection([('0','Esperando Envio'),
									('1','Aceptada por SUNAT'),
									('2','Rechazada'),
									('3','Enviado')],string=u'Estado de Envío',default='0',copy=False)

	print_web_version_pdf = fields.Char(string='Enlace PDF',copy=False)
	print_web_version_xml = fields.Char(string='Enlace XML',copy=False)
	file_name_pdf = fields.Char(copy=False)
	file_name_xml = fields.Char(copy=False)
	binary_version_pdf = fields.Binary(string='Version Binaria PDF',copy=False)
	binary_version_xml = fields.Binary(string='Version Binaria XML',copy=False)
	total_gross_weight = fields.Float(string='Peso Bruto Total',default=0)
	number_of_packages = fields.Float(string='Numero de Bultos',default=0)
	hash_code = fields.Char(string='Codigo Hash',copy=False)
	json_post = fields.Char(string='Json Enviado',copy=False,readonly=True)
	json_get = fields.Char(string='Json Respuesta',copy=False,readonly=True)

	def makecurrentsequecenumber(self, sequence_act):
		res = ''
		if sequence_act.prefix:
			res = sequence_act.prefix
		number = str(sequence_act.number_next_actual)
		if sequence_act.padding:
			number = number.rjust(sequence_act.padding, '0')
		res = res + number
		guide_line = self.env['remission.guide.series'].search([('series_id','=',sequence_act.id),('parameter_id.company_id','=',self.company_id.id)],limit=1)
		if guide_line:
			match = re.match(r'\bT+[0-9]{3}-[0-9]{1,}\b',res,re.I)
			if not match:
				raise UserError(u'El formato del número de guía "'+res+'" electrónica es incorrecto, el formato debe ser similar a "T000-00001".')
		return res

	@api.model
	def create(self,vals):
		t = super(StockPicking,self).create(vals)
		if t.serie_guia:
			guide_line = self.env['remission.guide.series'].search([('series_id','=',t.serie_guia.id),('parameter_id.company_id','=',self.env.company.id)],limit=1)
			if guide_line:
				t.electronic_guide = True
			else:
				t.electronic_guide = False
		else:
			t.electronic_guide = False
		return t

	def write(self,vals):
		if vals.get('serie_guia'):
			guide_line = self.env['remission.guide.series'].search([('series_id','=',vals['serie_guia']),('parameter_id.company_id','=',self.company_id.id)],limit=1)
			if guide_line:
				vals['electronic_guide'] = True
			else:
				vals['electronic_guide'] = False
		return super(StockPicking,self).write(vals)

	def verify_data_remission_guide(self):
		try:
			series_prefix = self.numberg[:4]
			series_number = int(self.numberg[5:])
		except ValueError:
			raise UserError(u'Ocurrió un error al obtener el número de guía')

		if not self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.code_sunat:
			raise UserError(u'Falta Tipo de Documento de Cliente')

		if not self.partner_id.commercial_partner_id.vat:
			raise UserError(u'Falta Nro de Documento de Cliente')

		if not self.partner_id.street:
			raise UserError(u'Falta Dirección de Cliente')

		if not self.reason_transfer:
			raise UserError(u'Falta Motivo de Traslado')

		if not self.type_of_transport:
			raise UserError(u'Falta Tipo de Transporte')

		if not self.carrier_id_it:
			raise UserError(u'Falta Transportista')

		if not self.carrier_id_it.l10n_latam_identification_type_id.code_sunat:
			raise UserError(u'Falta Tipo de Doc. de Transportista')

		if not self.carrier_id_it.vat:
			raise UserError(u'Falta Nro de Doc. de Transportista')

		if not self.driver_id:
			raise UserError(u'Falta Conductor')

		if not self.driver_id.l10n_latam_identification_type_id.code_sunat:
			raise UserError(u'Falta Tipo de Doc. de Conductor')

		if not self.driver_id.number_driver_licence:
			raise UserError(u'Falta Licencia de Conductor')

		if not self.starting_point:
			raise UserError(u'Falta punto de partida')

		if not self.picking_type_id.warehouse_id.partner_id.zip and not self.picking_type_id.warehouse_id.partner_id.district_id.code:
			raise UserError(u'Falta Ubigeo de partida')

		if not self.ending_point:
			raise UserError(u'Falta punto de llegada')

		if not self.partner_id.zip and not self.partner_id.district_id.code:
			raise UserError(u'Falta Ubigeo de llegada')

		if self.vehicle_id.license_plate and len(self.vehicle_id.license_plate)>8:
			raise UserError(u'La placa del vehículo (%s) excede los 8 caracteres' % (self.vehicle_id.license_plate))

		if self.electronic_guide:
			match = re.match(r'\bT+[0-9]{3}-[0-9]{1,}\b',self.numberg,re.I)
			if not match:
				raise UserError(u'El formato del número de guía "'+self.numberg+'" es incorrecto, el formato debe ser similar a "T000-00001"')

		return series_prefix,str(series_number)

	def get_preview_remission_guide(self):
		series,number = self.verify_data_remission_guide()
		module = __name__.split('addons.')[1].split('.')[0]
		wizard = self.env['preview.remission.guide.wizard'].create({
			'picking_id':self.id,
			'series':series,
			'number':number,
			'line_ids':[(0,0,{
				'move_id':m.id,
			}) for m in self.move_ids_without_package]
			})
		
		view='view_electronic_guide_wizard_form' if self.electronic_guide else 'view_remission_guide_wizard_form'
		return {
			'name':u'Previsualizar guía de Remisión',
			'res_id':wizard.id,
			'res_model': 'preview.remission.guide.wizard',
			'view_mode':'form',
			'view_id':self.env.ref('%s.%s'%(module,view)).id,
			'type': 'ir.actions.act_window',
			'target':'new',
		}