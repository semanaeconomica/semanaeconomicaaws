# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountCashRep(models.TransientModel):
	_name = 'account.cash.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en', required=True, default='pantalla')
	account_ids = fields.Many2many('account.account','account_book_account_cash_rel','id_cash_origen','id_account_destino',string=u'Cuentas', required=True)

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
		self.domain_dates()
		filtro = []

		self.env.cr.execute("""
			CREATE OR REPLACE view account_cash_book as ("""+self._get_sql()+""")""")

		if self.account_ids:
			cuentas_list = []
			for i in self.account_ids:
				cuentas_list.append(i.code)
			filtro.append( ('cuenta','in',tuple(cuentas_list)) )

		if self.type_show == 'pantalla':
			return {
				'name': 'Libro Caja Bancos',
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.cash.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel(filtro)
		
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			docname = 'LibroCajaBancos.csv'

			if self.account_ids:
				accounts_ids = self.account_ids.ids
				sql_accounts = " where account_id in (%s) " % (','.join(str(i) for i in accounts_ids))
				sql_query = """	COPY ("""+self._get_sql()+sql_accounts +""")TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			else:
				sql_query = """	COPY (select * from account_cash_book)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			
			self.env.cr.execute(sql_query)

			#Caracteres Especiales
			import importlib
			import sys
			importlib.reload(sys)

			f = open(direccion + docname, 'rb')		

			return self.env['popup.it'].get_file(docname,base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):

		sql = """select row_number() OVER () AS id,
		periodo, fecha, libro, voucher, cuenta,
		debe, haber,saldo, moneda, tc, debe_me, haber_me, saldo_me,
		code_cta_analitica, glosa, td_partner,doc_partner, partner, 
		td_sunat,nro_comprobante, fecha_doc, fecha_ven
		from get_caja_bancos('%s','%s',%s)
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

		workbook = Workbook(direccion +'LibroCajaBancos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO CAJA Y BANCOS############
		worksheet = workbook.add_worksheet("LIBRO CAJA Y BANCOS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','SALDO MN','MON','TC','DEBE ME', 'HABER ME', 'SALDO ME',
		'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.cash.book'].search(filtro):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.saldo if line.saldo else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,9,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line.debe_me if line.debe_me else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.haber_me if line.haber_me else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.saldo_me if line.saldo_me else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.code_cta_analitica if line.code_cta_analitica else '',formats['especial1'])
			worksheet.write(x,14,line.glosa if line.glosa else '',formats['especial1'])
			worksheet.write(x,15,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,16,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,17,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,18,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,19,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,20,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,21,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			x += 1

		widths = [10,9,7,11,8,10,10,12,5,7,11,11,11,17,47,4,11,40,3,16,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'LibroCajaBancos.xlsx', 'rb')
		return self.env['popup.it'].get_file('LibroCajaBancos.xlsx',base64.encodestring(b''.join(f.readlines())))

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