# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountHigherRep(models.TransientModel):
	_name = 'account.higher.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show = fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en', required=True, default='pantalla')
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
	account_ids = fields.Many2many('account.account','account_book_account_rel','id_higher_origen','id_account_destino',string=u'Cuentas', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
				self.date_ini = fiscal_year.date_from
				self.date_end = fiscal_year.date_to
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		filtro = []
		self.domain_dates()

		self.env.cr.execute("""
			CREATE OR REPLACE view account_higher_book as ("""+self._get_sql()+""")""")

		if self.account_ids:
			cuentas_list = []
			for i in self.account_ids:
				cuentas_list.append(i.code)
			filtro.append( ('cuenta','in',tuple(cuentas_list)) )

		if self.type_show == 'pantalla':
			return {
				'name': 'Libro Mayor Analitico',
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.higher.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel(filtro)
		
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')
			
			docname = 'LibroMayorAnalitico.csv'

			if self.account_ids:
				accounts_ids = self.account_ids.ids
				sql_accounts = " where account_id in (%s) " % (','.join(str(i) for i in accounts_ids))
				sql_query = """	COPY ("""+self._get_sql()+sql_accounts +""")TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			else:
				sql_query = """	COPY (select * from account_higher_book)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			
			self.env.cr.execute(sql_query)

			#Caracteres Especiales
			import importlib
			import sys
			importlib.reload(sys)

			f = open(direccion + docname, 'rb')		

			return self.env['popup.it'].get_file(docname,base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):

		if self.currency == 'pen':
			sql = """select row_number() OVER () AS id,
			periodo, fecha, libro, voucher, cuenta,
			debe, haber,balance,saldo, moneda, tc,
			code_cta_analitica, glosa, td_partner,doc_partner, partner, 
			td_sunat,nro_comprobante, fecha_doc, fecha_ven
			from get_mayor_detalle('%s','%s',%s)
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
		else:
			sql = """select row_number() OVER () AS id,
			periodo, fecha, libro, voucher, cuenta,
			debe_me as debe, haber_me as haber, balance_me as balance, saldo_me as saldo, moneda, tc,
			code_cta_analitica, glosa, td_partner,doc_partner, partner, 
			td_sunat,nro_comprobante, fecha_doc, fecha_ven
			from get_mayor_detalle('%s','%s',%s)
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
		
		return sql

	def get_excel(self,filtro):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libro_Mayor_Analitico.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO MAYOR ANALITICO############
		worksheet = workbook.add_worksheet("LIBRO MAYOR ANALITICO")
		worksheet.set_tab_color('blue')
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','SALDO','MON','TC',
				   'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMPROBANTE','FECHA DOC','FECHA VEN']
		x=1
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])

		for line in self.env['account.higher.book'].search(filtro):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.saldo if line.saldo else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,10,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,11,line.code_cta_analitica if line.code_cta_analitica else '',formats['especial1'])
			worksheet.write(x,12,line.glosa if line.glosa else '',formats['especial1'])
			worksheet.write(x,13,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,14,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,15,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,16,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,17,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,18,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,19,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			x += 1

		widths = [9,9,7,11,8,10,10,10,10,5,7,13,47,4,11,40,3,16,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libro_Mayor_Analitico.xlsx', 'rb')

		return self.env['popup.it'].get_file('Libro_Mayor_Analitico.xlsx',base64.encodestring(b''.join(f.readlines())))

	def domain_dates(self):
		if self.date_ini:
			if self.exercise.date_from.year != self.date_ini.year:
				raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_end:
			if self.exercise.date_from.year != self.date_end.year:
				raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_ini and self.date_end:
			if self.date_end < self.date_ini:
				raise UserError("La fecha final no puede ser menor a la fecha inicial.")