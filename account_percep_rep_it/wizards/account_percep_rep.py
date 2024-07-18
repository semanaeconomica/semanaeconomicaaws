# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountPercepRep(models.TransientModel):
	_name = 'account.percep.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True,default='pantalla')
	type =  fields.Selection([('solo','Solo Percepciones'),('det','Detalle Percepciones')],string=u'Mostrar', required=True,default='solo')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_txt(self,type,company_id,date_start,date_end):
		type_doc = self.env['main.parameter'].search([('company_id','=',company_id.id)],limit=1).dt_perception

		if not type_doc:
			raise UserError(u'No existe un Tipo de Documento para Percepciones configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#0621 + RUC + AÑO(YYYY) + MES(MM) + PI o P
		name_doc = "0621"+str(ruc)+str(date_start.year)+str('{:02d}'.format(date_start.month))

		if type == 1:
			name_doc += "PI.txt"
		if type == 0:
			name_doc += "P.txt"

		sql_query = self._get_sql_txt(type,date_start,date_end,company_id.id,type_doc.code)
		self.env.cr.execute(sql_query)
		sql_query = "COPY (%s) TO STDOUT WITH %s" % (sql_query, "CSV DELIMITER '|'")
		rollback_name = self._create_savepoint()

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_query, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			self._rollback_savepoint(rollback_name)

		res = res.decode('utf-8')

		return self.env['popup.it'].get_file(name_doc,res)

	@api.model
	def _create_savepoint(self):
		rollback_name = '%s_%s' % (
			self._name.replace('.', '_'), uuid.uuid1().hex)
		req = "SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)
		return rollback_name

	@api.model
	def _rollback_savepoint(self, rollback_name):
		req = "ROLLBACK TO SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)

	def _get_sql_txt(self,type,date_start,date_end,company_id,code):
		sql = ""
		if type == 0:
			sql = """select ruc_agente,serie_cp,numero_cp,to_char( fecha_com_per, 'dd/mm/yyyy'),percepcion,t_comp,serie_comp,numero_comp,to_char( fecha_cp, 'dd/mm/yyyy'),montof,campo
			from get_percepciones('%s','%s',%s) where tipo_comp = '%s'""" % (date_start.strftime('%Y/%m/%d'),date_end.strftime('%Y/%m/%d'),str(company_id),str(code))

		else:
			sql = """select ruc_agente,tipo_comp,serie_cp,numero_cp,to_char( fecha_com_per, 'dd/mm/yyyy'),percepcion,campo
			from get_percepciones('%s','%s',%s) where tipo_comp <> '%s'""" % (date_start.strftime('%Y/%m/%d'),date_end.strftime('%Y/%m/%d'),str(company_id),str(code))

		return sql

	def get_report(self):
		if self.type == 'solo':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_percep_sp_book as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Solo Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.percep.sp.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}
			if self.type_show == 'excel':
				return self.get_excel()
				
		if self.type == 'det':
			self.env.cr.execute("""
			CREATE OR REPLACE view account_percep_book
			 as ("""+self._get_sql(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
			if self.type_show == 'pantalla':
				return {
					'name': 'Detalle Percepciones',
					'type': 'ir.actions.act_window',
					'res_model': 'account.percep.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}
			if self.type_show == 'excel':
				return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		if self.type == 'solo':
			namefile = 'Solo_Percepciones.xlsx'
		if self.type == 'det':
			namefile = 'Detalle_Percepciones.xlsx'
		
		workbook = Workbook(direccion + namefile)
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		if self.type == 'solo':
			##########SOLO PERCEPCIONES############
			worksheet = workbook.add_worksheet("SOLO PERCEPCIONES")
		if self.type == 'det':
			##########DETALLE PERCEPCIONES############
			worksheet = workbook.add_worksheet("DETALLE PERCEPCIONES")

		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO CON','FECHA PERC','FECHA USO','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','SERIE',u'NÚMERO','FECHA COM PER','PERCEPCION']

		if self.type == 'det':
			HEADERS.append('TD COMP')
			HEADERS.append('SERIE COMP')
			HEADERS.append('NRO COMP')
			HEADERS.append('FECHA CP')
			HEADERS.append('MONTO')

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		if self.type == 'solo':
			dic = self.env['account.percep.sp.book'].search([])
		if self.type == 'det':
			dic = self.env['account.percep.book'].search([])

		for line in dic:
			worksheet.write(x,0,line.periodo_con if line.periodo_con else '',formats['especial1'])
			worksheet.write(x,1,line.periodo_percep if line.periodo_percep else '',formats['especial1'])
			worksheet.write(x,2,line.fecha_uso if line.fecha_uso else '',formats['dateformat'])
			worksheet.write(x,3,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,4,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,5,line.tipo_per if line.tipo_per else '',formats['especial1'])
			worksheet.write(x,6,line.ruc_agente if line.ruc_agente else '',formats['especial1'])
			worksheet.write(x,7,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,8,line.tipo_comp if line.tipo_comp else '',formats['especial1'])
			worksheet.write(x,9,line.serie_cp if line.serie_cp else '',formats['especial1'])
			worksheet.write(x,10,line.numero_cp if line.numero_cp else '',formats['especial1'])
			worksheet.write(x,11,line.fecha_com_per if line.fecha_com_per else '',formats['dateformat'])
			worksheet.write(x,12,line.percepcion if line.percepcion else '0.00',formats['numberdos'])
			if self.type == 'det':
				worksheet.write(x,13,line.t_comp if line.t_comp else '',formats['especial1'])
				worksheet.write(x,14,line.serie_comp if line.serie_comp else '',formats['especial1'])
				worksheet.write(x,15,line.numero_comp if line.numero_comp else '',formats['especial1'])
				worksheet.write(x,16,line.fecha_cp if line.fecha_cp else '',formats['dateformat'])
				worksheet.write(x,17,line.montof if line.montof else '0.00',formats['numberdos'])
			x += 1

		widths = [9,9,12,7,11,4,11,40,4,6,10,12,10]

		if self.type == 'det':
				widths.append(6)
				widths.append(7)
				widths.append(10)
				widths.append(10)

		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion + namefile, 'rb')
		return self.env['popup.it'].get_file(namefile,base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self,date_ini,date_end,company_id):

		if self.currency == 'pen':
			if self.type == 'solo':
				sql = """select row_number() OVER () AS id,
				periodo_con, periodo_percep, fecha_uso, libro,
				voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
				fecha_com_per, percepcion
				from get_percepciones_sp('%s','%s',%s)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					str(company_id))
				return sql

			else:
				sql = """select row_number() OVER () AS id,
				periodo_con, periodo_percep, fecha_uso, libro,
				voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
				fecha_com_per, percepcion, t_comp, serie_comp, numero_comp, fecha_cp, montof,campo
				from get_percepciones('%s','%s',%s)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					str(company_id))
				return sql
		else:
			if self.type == 'solo':
				sql = """select row_number() OVER () AS id,
				periodo_con, periodo_percep, fecha_uso, libro,
				voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
				fecha_com_per, percepcion_me as percepcion
				from get_percepciones_sp('%s','%s',%s)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					str(company_id))
				return sql

			else:
				sql = """select row_number() OVER () AS id,
				periodo_con, periodo_percep, fecha_uso, libro,
				voucher, tipo_per, ruc_agente, partner, tipo_comp, serie_cp, numero_cp,
				fecha_com_per, percepcion_me as percepcion, t_comp, serie_comp, numero_comp, fecha_cp, montof_me as montof,campo
				from get_percepciones('%s','%s',%s)
				""" % (date_ini.strftime('%Y/%m/%d'),
					date_end.strftime('%Y/%m/%d'),
					str(company_id))
				return sql
	