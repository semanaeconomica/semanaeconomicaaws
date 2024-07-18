# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import subprocess
import sys
import requests

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
	from suds.client import Client
except:
	install('suds-py3')


class ResPartner(models.Model):
	_inherit = 'res.partner'
	state_id = fields.Many2one('res.country.state', string='Departamento')
	province_id = fields.Many2one('res.country.state', string='Provincia')
	district_id = fields.Many2one('res.country.state', string='Distrito')

	####### CONSULTA DNI #########
	related_identification = fields.Char(related='l10n_latam_identification_type_id.code_sunat', store=True)
	n2_actv_econ = fields.Char(string='# Actividad Economica (A.C)')
	n2_actv_econ_1 = fields.Char(string='A.C Principal')
	n2_actv_econ_2 = fields.Char(string='A.C Secundaria 1')
	n2_actv_econ_3 = fields.Char(string='A.C Secundaria 2')
	n2_init_actv = fields.Char(string='Inicio de Actividad')
	n2_act_com_ext = fields.Char(string='Inicio de Actividad de Comercio Exterior')
	n2_afi_ple = fields.Char(string='Fecha Afiliacion al PLE')
	n2_cp_auto = fields.Char(string='Comprobantes autorizados')
	n2_dir_fiscal = fields.Char(string='Direccion Fiscal')
	n2_nom_comer = fields.Char(string='Nombre Comercial')
	n2_padrones = fields.Char(string='Padron')
	n2_sis_contab = fields.Char(string='Tipo de Sistema Contable')
	n2_see = fields.Char(string='Sistema de Emision Electronica')
	n2_tipo_contr = fields.Char(string='Tipo de Contrato')
	is_partner_retencion = fields.Boolean(string="Agente de Retención")
	direccion_complete_it = fields.Char(compute="get_adreess_it",string="Direccion Completa")
	direccion_complete_ubigeo_it = fields.Char(compute="get_adreess_it",string="Direccion Completa Ubigeo")


	@api.onchange('district_id')
	def change_distrito(self):
		for record in self:
			record.zip = record.district_id.code

	@api.depends('street', 'state_id','province_id', 'district_id', 'country_id', 'zip')
	def get_adreess_it(self):
		for record in self:
			direccioni = direccionf = record.street or ''
			if record.state_id or record.province_id or record.district_id or record.country_id:
				dep_pro_dis = f"{record.state_id.name or ''} - {record.province_id.name or ''} - {record.district_id.name or '' }"
				direccioni += ' ' + (dep_pro_dis if dep_pro_dis  else '' ) + ' , ' + (record.country_id.name if record.country_id else '')
				direccionf += ' ' + dep_pro_dis + ' , ' + (record.zip or '') + '  , ' + (record.country_id.name or '')
			record.direccion_complete_it = direccioni
			record.direccion_complete_ubigeo_it = direccionf

	@api.model
	def default_get(self, fields):
		res = super(ResPartner, self).default_get(fields)
		res['name'] = 'Nombre'
		res['name_p'] = 'Nombre'
		res['last_name'] = 'Apellido Paterno'
		res['m_last_name'] = 'Apellido Materno'
		return res

	@api.onchange('company_type')
	def _set_street_default(self):
		if self.company_type == 'company':
			if self.l10n_latam_identification_type_id:
				if self.l10n_latam_identification_type_id.code_sunat == '06':
					self.street = 'Calle'
		else:
			self.street = ''

	@api.onchange('l10n_latam_identification_type_id')
	def _verify_document(self):
		if self.l10n_latam_identification_type_id:
			if self.l10n_latam_identification_type_id.code_sunat == '06' and self.company_type == 'company':
				self.street = 'Calle'
			else:
				self.street = ''
		else:
			self.street = ''

	def verify_dni(self):

		parameters = self.env['sale.main.parameter'].verify_query_parameters()
		if not self.vat:
			raise UserError("Debe seleccionar un DNI")
		if parameters.query_supplier == '1':
			client = Client(parameters.query_dni_url, faults=False, cachingpolicy=1, location=parameters.query_dni_url)
			try:
				result = client.service.consultar(str(self.vat), parameters.query_email, parameters.query_token,
												parameters.query_type)
			except Exception as e:
				raise UserError('No se encontro el DNI')
			texto = result[1].split('|')
			flag = False
			nombres = ''
			a_paterno = ''
			a_materno = ''

			for c in texto:
				tmp = c.split('=')
				if tmp[0] == 'status_id' and tmp[1] == '102':
					raise UserError('El DNI debe tener al menos 8 digitos de longitud')
				if tmp[0] == 'status_id' and tmp[1] == '103':
					raise UserError('El DNI debe ser un valor numerico')
				if tmp[0] == 'reniec_nombres' and tmp[1] != '':
					nombres = tmp[1]
					self.name_p = tmp[1]
				if tmp[0] == 'reniec_paterno' and tmp[1] != '':
					a_paterno = tmp[1]
					self.last_name = tmp[1]
				if tmp[0] == 'reniec_materno' and tmp[1] != '':
					a_materno = tmp[1]
					self.m_last_name = tmp[1]
			self.name = (nombres + " " + a_paterno + " " + a_materno).strip()
		else:
			params = {
						"token": parameters.migo_token,
						"dni": self.vat
					}
			
			url = 'https://api.migo.pe/api/v1/dni'
			
			headers = requests.utils.default_headers()
			headers['Content-Type'] = 'application/json'
			headers['Accept'] = 'application/json'
			try:
				response = requests.post(url, headers=headers, params=params)
				jsson = response.json() #response.text
				flag = jsson['success']

			except Exception as err:
				raise UserError(err)
			
			if flag:
				if jsson['nombre']:
					nombres = jsson['nombre'].split(' ')
					a_paterno = nombres[0]
					self.last_name = nombres[0]
					a_materno = nombres[1]
					self.m_last_name = nombres[1]
					nombres = jsson['nombre'].replace(a_paterno+ ' '+a_materno+' ','')
					self.name_p = jsson['nombre'].replace(a_paterno+ ' '+a_materno+' ','')
					self.name = (nombres + " " + a_paterno + " " + a_materno).strip()

	####### CONSULTA DNI #########

	####### CONSULTA RUC #########
	ruc_state = fields.Char(string='RUC Estado')
	ruc_condition = fields.Char(string=u'RUC Condición')

	def verify_ruc(selfs):
		for self in selfs:
			#if self.l10n_latam_identification_type_id == self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1).dt_sunat_ruc:
			if self.l10n_latam_identification_type_id.code_sunat == '6':
				parameters = self.env['sale.main.parameter'].verify_query_parameters()
				if parameters.query_supplier == '1':
					client = Client(parameters.query_ruc_url, faults=False, cachingpolicy=1,
									location=parameters.query_ruc_url)
					result = client.service.consultaRUC(self.vat, parameters.query_email, parameters.query_token,
														parameters.query_type)
					texto = result[1].split('|')
					flag = False

					for i in texto:
						tmp = i.split('=')
						if tmp[0] == 'status_id' and tmp[1] == '1':
							flag = True

					# obtner el distrito - provincia - departamento
					departamento_string = provincia_string = distrito_string = dep_pro_dis = None
					for j in texto:
						tmp = j.split('=')
						if tmp[0] == 'n1_ubigeo_dep':
							departamento_string = tmp[1]
						if tmp[0] == 'n1_ubigeo_pro':
							provincia_string = tmp[1]
						if tmp[0] == 'n1_ubigeo_dis':
							distrito_string = tmp[1]
					if departamento_string and provincia_string and distrito_string:
						dep_pro_dis = f"{departamento_string} - {provincia_string} - {distrito_string}"

					if flag:
						for j in texto:
							tmp = j.split('=')
							if tmp[0] == 'n1_alias':
								self.name = tmp[1]
							if tmp[0] == 'n1_direccion':
								# obtener la direccion
								direccionx = tmp[1]
								# quitar el pais - distrito - departamento
								if dep_pro_dis:
									direccionx = direccionx.replace(dep_pro_dis, '')
								# raise ValueError(direccionx)
								self.street = direccionx

							for ar in ['n2_actv_econ', 'n2_actv_econ_1', 'n2_actv_econ_2', 'n2_actv_econ_3',
									'n2_init_actv',
									'n2_act_com_ext', 'n2_tipo_contr',
									'n2_afi_ple', 'n2_cp_auto', 'n2_dir_fiscal', 'n2_nom_comer',
									'n2_padrones', 'n2_sis_contab', 'n2_see']:
								if tmp[0] == ar:
									self[ar] = str(tmp[1])

							if tmp[0] == 'n1_ubigeo':
								ubi_t = tmp[1]
								ubigeo = self.env['res.country.state'].search([('code', '=', ubi_t)])

								if ubigeo:
									self.zip = tmp[1]
									pais = self.env['res.country'].search([('code', '=', 'PE')])
									ubidepa = ubi_t[0:2]
									ubiprov = ubi_t[0:4]
									ubidist = ubi_t[0:6]

									departamento = self.env['res.country.state'].search(
										[('code', '=', ubidepa), ('country_id', '=', pais.id)])
									provincia = self.env['res.country.state'].search(
										[('code', '=', ubiprov), ('country_id', '=', pais.id)])
									distrito = self.env['res.country.state'].search(
										[('code', '=', ubidist), ('country_id', '=', pais.id)])

									self.country_id = pais.id
									self.state_id = departamento.id
									self.province_id = provincia.id
									self.district_id = distrito.id
							if tmp[0] == 'n1_estado':
								self.ruc_state = tmp[1]
							if tmp[0] == 'n1_condicion':
								self.ruc_condition = tmp[1]

					else:
						raise UserError("El RUC es invalido.")
					
				else:
					params = {
								"token": parameters.migo_token,
								"ruc": self.vat
							}
					
					url = 'https://api.migo.pe/api/v1/ruc'
					url_actividad = 'https://api.migo.pe/api/v1/ruc/actividad/{ruc}?token={token}'.format(ruc = self.vat,token = parameters.migo_token)
					
					headers = requests.utils.default_headers()
					headers['Content-Type'] = 'application/json'
					headers['Accept'] = 'application/json'
					try:
						response = requests.post(url, headers=headers, params=params)
						response_actividad = requests.get(url_actividad, headers=headers)
						jsson = response.json() #response.text
						jsson_actividad = response_actividad.json() #response.text
						flag = jsson['success']
						flag_actividad = jsson_actividad['success']

					except Exception as err:
						raise UserError(err)
					
					if flag:
						if jsson['nombre_o_razon_social']:
							self.name = jsson['nombre_o_razon_social']
						if jsson['direccion_simple']:
							self.street = jsson['direccion_simple']
						if jsson['ubigeo'] != '-':
							ubigeo=self.env['res.country.state'].search([('code','=',jsson['ubigeo'])])
							if ubigeo:
								self.zip = jsson['ubigeo']
								pais =self.env['res.country'].search([('code','=','PE')]) 
								ubidepa=jsson['ubigeo'][0:2]
								ubiprov=jsson['ubigeo'][0:4]
								ubidist=jsson['ubigeo'][0:6]

								departamento = self.env['res.country.state'].search([('code','=',ubidepa),('country_id','=',pais.id)])
								provincia  = self.env['res.country.state'].search([('code','=',ubiprov),('country_id','=',pais.id)])
								distrito = self.env['res.country.state'].search([('code','=',ubidist),('country_id','=',pais.id)])

								self.country_id=pais.id
								self.state_id=departamento.id
								self.province_id = provincia.id
								self.district_id = distrito.id
						if jsson['estado_del_contribuyente']:
							self.ruc_state = jsson['estado_del_contribuyente']
						if jsson['condicion_de_domicilio']:
							self.ruc_condition = jsson['condicion_de_domicilio']
							
					else:
						raise UserError("El RUC es invalido.")
					if flag_actividad:
						if jsson_actividad['actividad_economica_rev3_principal']:
							self.n2_actv_econ_1 = jsson_actividad['actividad_economica_rev3_principal']
							self.n2_actv_econ_2 = jsson_actividad['actividad_economica_rev3_secundaria']
							self.n2_actv_econ_3 = jsson_actividad['actividad_economica_rev4_principal']

			if self.l10n_latam_identification_type_id.code_sunat == '1':
				self.verify_dni()

	####### CONSULTA RUC #########
