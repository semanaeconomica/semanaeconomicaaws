# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountSaleeRep(models.TransientModel):
	_name = 'account.sale.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('csv','CSV')],string=u'Mostrar en',default='pantalla')
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)

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
		if self.type_show:
			self.env.cr.execute("""
				CREATE OR REPLACE view account_sale_book as ("""+self._get_sql()+""")""")
				
			if self.type_show == 'pantalla':
				return {
					'name': 'Registro Ventas',
					'type': 'ir.actions.act_window',
					'res_model': 'account.sale.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}

			if self.type_show == 'excel':
				return self.get_excel()
			
			if self.type_show == 'csv':
				return self.getCsv()
		else:
			raise UserError("Es que complete el campo Mostrar en")

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Ventas.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO VENTAS############
		worksheet = workbook.add_worksheet("REGISTRO VENTAS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
		'EXP','VENTA G','INAF','EXO','ISC V','ICBPER','OTROS V','IGV','TOTAL','MON','MONTO ME','TC','FECHA DET','COMP DET',
		'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		#DECLARANDO TOTALES
		exp, venta_g, inaf, exo, isc_v, otros_v, icbper, igv_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for line in self.env['account.sale.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha_cont if line.fecha_cont else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.fecha_e if line.fecha_e else '',formats['dateformat'])
			worksheet.write(x,5,line.fecha_v if line.fecha_v else '',formats['dateformat'])
			worksheet.write(x,6,line.td if line.td else '',formats['especial1'])
			worksheet.write(x,7,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,8,line.anio if line.anio else '',formats['especial1'])
			worksheet.write(x,9,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,10,line.tdp if line.tdp else '',formats['especial1'])
			worksheet.write(x,11,line.docp if line.docp else '',formats['especial1'])
			worksheet.write(x,12,line.namep if line.namep else '',formats['especial1'])
			worksheet.write(x,13,line.exp if line.exp else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.venta_g if line.venta_g else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.inaf if line.inaf else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.exo if line.exo else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.isc_v if line.isc_v else '0.00',formats['numberdos'])
			worksheet.write(x,18,line.icbper if line.icbper else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.otros_v if line.otros_v else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.igv_v if line.igv_v else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.total if line.total else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,23,line.monto_me if line.monto_me else '0.00',formats['numberdos'])
			worksheet.write(x,24,line.currency_rate if line.currency_rate else '0.0000',formats['numbercuatro'])
			worksheet.write(x,25,line.fecha_det if line.fecha_det else '',formats['dateformat'])
			worksheet.write(x,26,line.comp_det if line.comp_det else '',formats['especial1'])
			worksheet.write(x,27,line.f_doc_m if line.f_doc_m else '',formats['dateformat'])
			worksheet.write(x,28,line.td_doc_m if line.td_doc_m else '',formats['especial1'])
			worksheet.write(x,29,line.serie_m if line.serie_m else '',formats['especial1'])
			worksheet.write(x,30,line.numero_m if line.numero_m else '',formats['especial1'])
			worksheet.write(x,31,line.glosa if line.glosa else '',formats['especial1'])
			x += 1

			exp += line.exp if line.exp else 0
			venta_g += line.venta_g if line.venta_g else 0
			inaf += line.inaf if line.inaf else 0
			exo += line.exo if line.exo else 0
			isc_v += line.isc_v if line.isc_v else 0
			otros_v += line.otros_v if line.otros_v else 0
			icbper += line.icbper if line.icbper else 0
			igv_v += line.igv_v if line.igv_v else 0
			total += line.total if line.total else 0

		worksheet.write(x,13,exp,formats['numbertotal'])
		worksheet.write(x,14,venta_g,formats['numbertotal'])
		worksheet.write(x,15,inaf,formats['numbertotal'])
		worksheet.write(x,16,exo,formats['numbertotal'])
		worksheet.write(x,17,isc_v,formats['numbertotal'])
		worksheet.write(x,18,icbper,formats['numbertotal'])
		worksheet.write(x,19,otros_v,formats['numbertotal'])
		worksheet.write(x,20,igv_v,formats['numbertotal'])
		worksheet.write(x,21,total,formats['numbertotal'])

		widths = [9,12,7,11,10,10,3,10,10,10,4,11,40,10,10,10,10,10,10,10,10,12,5,12,7,12,12,12,12,12,12,47]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Ventas.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro Ventas.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getCsv(self):
		docname = 'Registro Ventas.csv'

		#Get CSV
		sql_query = """select * from account_sale_book"""
		self.env.cr.execute(sql_query)
		sql_query = "COPY (%s) TO STDOUT WITH %s" % (sql_query, "CSV DELIMITER ','")
		rollback_name = self._create_savepoint()

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_query, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			self._rollback_savepoint(rollback_name)

		res = res.decode('utf-8')

		return self.env['popup.it'].get_file(docname,res)

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

	def _get_sql_ple141(self,x_date_ini,x_date_end,x_company_id):
		sql = """SELECT 
				vst_v.periodo || '00' as campo1,
				vst_v.periodo || vst_v.libro || vst_v.voucher as campo2,
				'M' || vst_v.voucher as campo3,
				TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_v.td = '14' THEN TO_CHAR(vst_v.fecha_v :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_v.td is not null THEN vst_v.td
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_v.serie is not null THEN vst_v.serie
					ELSE NULL
				END AS campo7,
				CASE
					WHEN vst_v.numero is not null THEN vst_v.numero
					ELSE NULL
				END AS campo8,
				CASE
					WHEN (am.campo_09_sale is not null) and (vst_v.td = '00' or vst_v.td = '03' or vst_v.td = '12' or vst_v.td = '13' or vst_v.td = '87') THEN am.campo_09_sale
					ELSE NULL
				END AS campo9,
				CASE
					WHEN vst_v.tdp is not null THEN vst_v.tdp
					ELSE NULL
				END AS campo10,
				CASE
					WHEN vst_v.docp is not null THEN vst_v.docp
					ELSE NULL
				END AS campo11,
				CASE
					WHEN vst_v.namep is not null THEN vst_v.namep
					ELSE NULL
				END AS campo12,
				CASE
					WHEN vst_v.exp is not null THEN TRUNC(vst_v.exp,2)
					ELSE TRUNC(0,2)
				END AS campo13,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo14,
				CASE
					WHEN (am.is_descount = True) and vst_v.venta_g is not null THEN TRUNC(vst_v.venta_g,2)
					ELSE TRUNC(0,2)
				END AS campo15,
				CASE
					WHEN (am.is_descount is null or am.is_descount = False) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo16,
				CASE
					WHEN (am.is_descount = True) and vst_v.igv_v is not null THEN TRUNC(vst_v.igv_v,2)
					ELSE TRUNC(0,2)
				END AS campo17,
				CASE
					WHEN vst_v.exo is not null THEN TRUNC(vst_v.exo,2)
					ELSE TRUNC(0,2)
				END AS campo18,
				CASE
					WHEN vst_v.inaf is not null THEN TRUNC(vst_v.inaf,2)
					ELSE TRUNC(0,2)
				END AS campo19,
				CASE
					WHEN vst_v.isc_v is not null THEN TRUNC(vst_v.isc_v,2)
					ELSE TRUNC(0,2)
				END AS campo20,
				TRUNC(0,2) as campo21,
				TRUNC(0,2) as campo22,
				CASE
					WHEN vst_v.icbper is not null THEN TRUNC(vst_v.icbper,2)
					ELSE TRUNC(0,2)
				END AS campo23,
				CASE
					WHEN vst_v.otros_v is not null THEN TRUNC(vst_v.otros_v,2)
					ELSE TRUNC(0,2)
				END AS campo24,
				CASE
					WHEN vst_v.total is not null THEN TRUNC(vst_v.total,2)
					ELSE TRUNC(0,2)
				END AS campo25,
				vst_v.name AS campo26,
				vst_v.currency_rate::numeric(12,3) as campo27,
				CASE
					WHEN vst_v.f_doc_m is not null THEN TO_CHAR(vst_v.f_doc_m :: DATE, 'dd/mm/yyyy')
					ELSE NULL
				END AS campo28,
				CASE
					WHEN vst_v.td_doc_m is not null THEN vst_v.td_doc_m
					ELSE NULL
				END AS campo29,
				CASE
					WHEN vst_v.serie_m is not null OR vst_v.serie_m <> '' THEN vst_v.serie_m
					ELSE NULL
				END AS campo30,
				CASE
					WHEN vst_v.numero_m is not null THEN vst_v.numero_m
					ELSE NULL
				END AS campo31,
				NULL AS campo32,
				CASE
					WHEN am.campo_32_sale = True THEN '1'
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_33_sale = True THEN '1'
					ELSE NULL
				END AS campo34,
				am.campo_34_sale AS campo35,
				NULL AS campo36
				FROM vst_ventas_1_1 vst_v
				LEFT JOIN account_move am ON am.id = vst_v.am_id
				WHERE (vst_v.fecha_cont between '%s' and '%s')
				and vst_v.company = %s 
				ORDER BY vst_v.periodo, vst_v.libro, vst_v.voucher
			""" % (x_date_ini.strftime('%Y/%m/%d'),
					x_date_end.strftime('%Y/%m/%d'),
					str(x_company_id))

		return sql

	def _get_sql(self):
		
		if self.currency == 'pen':
			sql = """select row_number() OVER () AS id,
					periodo, fecha_cont, libro, voucher, fecha_e, fecha_v, td, 
					serie, anio, numero, tdp, docp, namep, exp, venta_g, inaf, exo, isc_v, icbper,
					otros_v, igv_v, total, name, monto_me, currency_rate, fecha_det, 
					comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa
					from vst_ventas_1_1
					where (fecha_cont between '%s' and '%s')
					and company = %s 
				""" % (self.date_ini.strftime('%Y/%m/%d'),
					self.date_end.strftime('%Y/%m/%d'),
					str(self.company_id.id))
		else:
			sql = """SELECT row_number() OVER () AS id,
					vst1.periodo, vst1.fecha_cont, vst1.libro, vst1.voucher, vst1.fecha_e, vst1.fecha_v, vst1.td, 
					vst1.serie, vst1.anio, vst1.numero, vst1.tdp, vst1.docp, vst1.namep, 
					vst2.expme as exp, vst2.ventagme as venta_g, vst2.inafme as inaf, vst2.exome as exo, vst2.iscme as isc_v, 
					vst2.icbperme as icbper, vst2.otrosme as otros_v, vst2.igvme as igv_v, 
					(vst2.expme + vst2.ventagme + vst2.inafme + vst2.exome + vst2.iscme +
					vst2.icbperme + vst2.otrosme + vst2.igvme) as total, 
					vst1.name, vst1.monto_me, vst1.currency_rate, vst1.fecha_det, 
					vst1.comp_det, vst1.f_doc_m, vst1.td_doc_m, vst1.serie_m, vst1.numero_m, vst1.glosa
					FROM vst_ventas_1_1 vst1
					LEFT JOIN vst_ventas_1_bm vst2 ON vst1.am_id = vst2.move_id
					where (vst1.fecha_cont between '%s' and '%s')
					and vst1.company = %s 
				""" % (self.date_ini.strftime('%Y/%m/%d'),
					self.date_end.strftime('%Y/%m/%d'),
					str(self.company_id.id))

		return sql

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