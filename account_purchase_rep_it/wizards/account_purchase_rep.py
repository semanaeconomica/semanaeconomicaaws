# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid

class AccountPurchaseRep(models.TransientModel):
	_name = 'account.purchase.rep'

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
				CREATE OR REPLACE view account_purchase_book as ("""+self._get_sql()+""")""")
				
			if self.type_show == 'pantalla':
				return {
					'name': 'Registro Compras',
					'type': 'ir.actions.act_window',
					'res_model': 'account.purchase.book',
					'view_mode': 'tree',
					'view_type': 'form',
					'views': [(False, 'tree')],
				}

			if self.type_show == 'excel':
				return self.get_excel()
			
			if self.type_show == 'csv':
				return self.getCsv()
		else:
			raise UserError("Es necesario completar el campo Mostrar en")

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_Compras.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########REGISTRO COMPRAS############
		worksheet = workbook.add_worksheet("REGISTRO COMPRAS")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA CONT','LIBRO','VOUCHER','FECHA EM','FECHA VEN','TD','SERIE',u'AÑO',u'NÚMERO','TDP','RUC','PARTNER',
		'BIOGYE','BIOGEYNG','BIONG','CNG','ISC','ICBPER','OTROS','IGV 1','IGV 2','IGV 3','TOTAL','MON','MONTO ME','TC','FECHA DET','COMP DET',
		'FECHA DOC M','TD DOC M','SERIE M','NUMERO M','GLOSA']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		#DECLARANDO TOTALES
		base1, base2, base3, cng, isc, otros, icbper, igv1, igv2, igv3, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for line in self.env['account.purchase.book'].search([]):
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
			worksheet.write(x,13,line.base1 if line.base1 else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.base2 if line.base2 else '0.00',formats['numberdos'])
			worksheet.write(x,15,line.base3 if line.base3 else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.cng if line.cng else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.isc if line.isc else '0.00',formats['numberdos'])
			worksheet.write(x,18,line.icbper if line.icbper else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.otros if line.otros else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.igv1 if line.igv1 else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.igv2 if line.igv2 else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.igv3 if line.igv3 else '0.00',formats['numberdos'])
			worksheet.write(x,23,line.total if line.total else '0.00',formats['numberdos'])
			worksheet.write(x,24,line.name if line.name else '',formats['especial1'])
			worksheet.write(x,25,line.monto_me if line.monto_me else '0.00',formats['numberdos'])
			worksheet.write(x,26,line.currency_rate if line.currency_rate else '0.0000',formats['numbercuatro'])
			worksheet.write(x,27,line.fecha_det if line.fecha_det else '',formats['dateformat'])
			worksheet.write(x,28,line.comp_det if line.comp_det else '',formats['especial1'])
			worksheet.write(x,29,line.f_doc_m if line.f_doc_m else '',formats['dateformat'])
			worksheet.write(x,30,line.td_doc_m if line.td_doc_m else '',formats['especial1'])
			worksheet.write(x,31,line.serie_m if line.serie_m else '',formats['especial1'])
			worksheet.write(x,32,line.numero_m if line.numero_m else '',formats['especial1'])
			worksheet.write(x,33,line.glosa if line.glosa else '',formats['especial1'])

			base1 += line.base1 if line.base1 else 0
			base2 += line.base2 if line.base2 else 0
			base3 += line.base3 if line.base3 else 0
			cng += line.cng if line.cng else 0
			isc += line.isc if line.isc else 0
			icbper += line.icbper if line.icbper else 0
			otros += line.otros if line.otros else 0
			igv1 += line.igv1 if line.igv1 else 0
			igv2 += line.igv2 if line.igv2 else 0
			igv3 += line.igv3 if line.igv3 else 0
			total += line.total if line.total else 0

			x += 1

		#TOTALES

		worksheet.write(x,13,base1,formats['numbertotal'])
		worksheet.write(x,14,base2,formats['numbertotal'])
		worksheet.write(x,15,base3,formats['numbertotal'])
		worksheet.write(x,16,cng,formats['numbertotal'])
		worksheet.write(x,17,isc,formats['numbertotal'])
		worksheet.write(x,18,icbper,formats['numbertotal'])
		worksheet.write(x,19,otros,formats['numbertotal'])
		worksheet.write(x,20,igv1,formats['numbertotal'])
		worksheet.write(x,21,igv2,formats['numbertotal'])
		worksheet.write(x,22,igv3,formats['numbertotal'])
		worksheet.write(x,23,total,formats['numbertotal'])

		widths = [9,12,7,11,10,10,3,10,10,10,4,11,40,10,10,10,10,10,10,10,10,10,10,12,5,12,7,12,12,12,12,12,12,47]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_Compras.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro Compras.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getCsv(self):
		docname = 'Registro Compras.csv'

		#Get CSV
		sql_query = """select * from account_purchase_book"""
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


	def _get_sql(self):
		if self.currency == 'pen':
			sql = """SELECT row_number() OVER () AS id,
				periodo, fecha_cont, libro, voucher, fecha_e, fecha_v, td, serie, anio, numero, tdp, docp,
				namep, base1, base2, base3, cng, isc, icbper, otros, igv1, igv2, igv3, total, name, monto_me,
				currency_rate, fecha_det, comp_det, f_doc_m, td_doc_m, serie_m, numero_m, glosa 
				FROM vst_compras_1_1
				WHERE (fecha_cont between '%s' AND '%s')
				AND company = %s 
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
		else:
			sql = """SELECT row_number() OVER () AS id,
				vst1.periodo, vst1.fecha_cont, vst1.libro, vst1.voucher, vst1.fecha_e,
				vst1.fecha_v, vst1.td, vst1.serie, vst1.anio, vst1.numero, vst1.tdp, vst1.docp,
				vst1.namep, vst2.base1me AS base1, vst2.base2me AS base2, vst2.base3me AS base3, vst2.cngme AS cng, 
				vst2.iscme AS isc, vst2.icbperme AS icbper, vst2.otrosme AS otros, vst2.igv1me AS igv1, vst2.igv2me AS igv2, vst2.igv3me AS igv3, 
				(vst2.base1me + vst2.base2me + vst2.base3me + vst2.cngme + vst2.iscme + vst2.otrosme + vst2.icbperme +
				vst2.igv1me + vst2.igv2me + vst2.igv3me) AS total, vst1.name, vst1.monto_me,
				vst1.currency_rate, vst1.fecha_det, vst1.comp_det, vst1.f_doc_m, vst1.td_doc_m, vst1.serie_m, vst1.numero_m, vst1.glosa 
				FROM vst_compras_1_1 vst1
				LEFT JOIN vst_compras_1_bm vst2 ON vst1.am_id = vst2.move_id
				WHERE (vst1.fecha_cont between '%s' AND '%s')
				AND vst1.company = %s 
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

		return sql

	def _get_sql_ple81(self,x_date_ini,x_date_end,x_company_id):
		sql = """select vst_c.periodo || '00' as campo1,
			vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
			'M' || vst_c.voucher as campo3,
			TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
			CASE
				WHEN vst_c.td = '14' THEN TO_CHAR(vst_c.fecha_v :: DATE, 'dd/mm/yyyy')
				ELSE NULL
			END AS campo5,
			CASE
				WHEN vst_c.td is null THEN NULL
				ELSE vst_c.td
			END AS campo6,
			CASE
				WHEN vst_c.serie is not null or vst_c.serie <> '' THEN vst_c.serie
				ELSE NULL
			END AS campo7,
			CASE
				WHEN vst_c.anio is not null THEN vst_c.anio
				ELSE NULL
			END AS campo8,
			CASE
				WHEN vst_c.numero is not null THEN vst_c.numero
				ELSE NULL
			END AS campo9,
			NULL as campo10,
			vst_c.tdp as campo11,
			vst_c.docp as campo12,
			vst_c.namep as campo13,
			TRUNC(vst_c.base1,2) as campo14,
			TRUNC(vst_c.igv1,2) as campo15,
			TRUNC(vst_c.base2,2) as campo16,
			TRUNC(vst_c.igv2,2) as campo17,
			TRUNC(vst_c.base3,2) as campo18,
			TRUNC(vst_c.igv3,2) as campo19,
			TRUNC(vst_c.cng,2) as campo20,
			TRUNC(vst_c.isc,2) as campo21,
			TRUNC(vst_c.icbper,2) as campo22,
			TRUNC(vst_c.otros,2) as campo23,
			TRUNC(vst_c.total,2) as campo24,
			vst_c.name as campo25,
			vst_c.currency_rate::numeric(12,3) as campo26,
			CASE
				WHEN vst_c.f_doc_m is not null THEN TO_CHAR(vst_c.f_doc_m :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo27,
			CASE
				WHEN vst_c.td_doc_m is not null THEN vst_c.td_doc_m
				ELSE NULL
			END AS campo28,
			CASE
				WHEN vst_c.serie_m is not null or vst_c.serie_m <> '' THEN vst_c.serie_m
				ELSE NULL
			END AS campo29,
			CASE
				WHEN (vst_c.td_doc_m = '50' or vst_c.td_doc_m = '52') and vst_c.serie_m is not null THEN vst_c.serie_m
				ELSE NULL
			END AS campo30,
			CASE
				WHEN vst_c.numero_m is not null THEN vst_c.numero_m
				ELSE NULL
			END AS campo31,
			CASE
				WHEN vst_c.fecha_det is not null THEN TO_CHAR(vst_c.fecha_det :: DATE, 'dd/mm/yyyy') 
				ELSE NULL
			END AS campo32,
			CASE
				WHEN vst_c.comp_det is not null THEN vst_c.comp_det
				ELSE NULL
			END AS campo33,
			CASE
				WHEN am.campo_33_purchase = True THEN '1'
				ELSE NULL
			END AS campo34,
			CASE
				WHEN am.campo_34_purchase is not null THEN am.campo_34_purchase
				ELSE NULL
			END AS campo35,
			CASE
				WHEN am.campo_35_purchase is not null THEN am.campo_35_purchase
				ELSE NULL
			END AS campo36,
			CASE
				WHEN am.campo_36_purchase = True THEN '1'
				ELSE NULL
			END AS campo37,
			CASE
				WHEN am.campo_37_purchase = True THEN '1'
				ELSE NULL
			END AS campo38,
			CASE
				WHEN am.campo_38_purchase = True THEN '1'
				ELSE NULL
			END AS campo39,
			CASE
				WHEN am.campo_39_purchase = True THEN '1'
				ELSE NULL
			END AS campo40,
			CASE
				WHEN am.campo_40_purchase = True THEN '1'
				ELSE NULL
			END AS campo41,
			CASE
				WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
				ELSE NULL
			END AS campo42,
			NULL AS campo43
			from vst_compras_1_1 vst_c
			left join account_move am on am.id = vst_c.am_id
			where (vst_c.fecha_cont between '%s' and '%s') and vst_c.company = %s
			and vst_c.td not in ('91','97','98')
			ORDER BY vst_c.periodo, vst_c.libro, vst_c.voucher
				""" % (x_date_ini.strftime('%Y/%m/%d'),
			x_date_end.strftime('%Y/%m/%d'),
			str(x_company_id))

		return sql

	def _get_sql_ple82(self,x_date_ini,x_date_end,x_company_id):
		sql = """select 
				vst_c.periodo || '00' as campo1,
				vst_c.periodo || vst_c.libro || vst_c.voucher as campo2,
				'M' || vst_c.voucher as campo3,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') as campo4,
				CASE
					WHEN vst_c.td is not null THEN vst_c.td
					ELSE NULL
				END AS campo5,
				CASE
					WHEN vst_c.serie is not null THEN vst_c.serie
					ELSE NULL
				END AS campo6,
				CASE
					WHEN vst_c.numero is not null THEN vst_c.numero
					ELSE NULL
				END AS campo7,
				CASE
					WHEN vst_c.cng is not null THEN vst_c.cng
					ELSE 0.00
				END AS campo8,
				CASE
					WHEN vst_c.otros is not null THEN vst_c.otros
					ELSE 0.00
				END AS campo9,
				CASE
					WHEN vst_c.total is not null THEN vst_c.total
					ELSE 0.00
				END AS campo10,
				CASE
					WHEN ec01.code is not null THEN ec01.code
					ELSE NULL
				END AS campo11,
				CASE
					WHEN am.campo_12_purchase_nd is not null THEN am.campo_12_purchase_nd
					ELSE NULL
				END AS campo12,
				CASE
					WHEN am.campo_13_purchase_nd is not null THEN am.campo_13_purchase_nd
					ELSE NULL
				END AS campo13,
				CASE
					WHEN am.campo_14_purchase_nd is not null THEN am.campo_14_purchase_nd
					ELSE NULL
				END AS campo14,
				CASE
					WHEN am.campo_15_purchase_nd is not null THEN am.campo_15_purchase_nd
					ELSE 0
				END AS campo15,
				vst_c.name AS campo16,
				vst_c.currency_rate::numeric(12,3) as campo17,
				CASE
					WHEN rp1.country_home_nd is not null THEN rp1.country_home_nd
					ELSE NULL
				END AS campo18,
				vst_c.namep as campo19,
				CASE
					WHEN rp1.home_nd is not null THEN rp1.home_nd
					ELSE NULL
				END AS campo20,
				CASE
					WHEN vst_c.docp is not null THEN vst_c.docp
					ELSE NULL
				END AS campo21,
				CASE
					WHEN rp1.ide_nd is not null THEN rp1.ide_nd
					ELSE NULL
				END AS campo22,
				CASE
					WHEN rp2.name is not null THEN rp2.name
					ELSE NULL
				END AS campo23,
				CASE
					WHEN rp2.country_home_nd is not null THEN rp2.country_home_nd
					ELSE NULL
				END AS campo24,
				CASE
					WHEN rp1.v_con_nd is not null THEN rp1.v_con_nd
					ELSE NULL
				END AS campo25,
				CASE
					WHEN am.campo_26_purchase_nd is not null THEN am.campo_26_purchase_nd
					ELSE 0
				END AS campo26,
				CASE
					WHEN am.campo_27_purchase_nd is not null THEN am.campo_27_purchase_nd
					ELSE 0
				END AS campo27,
				CASE
					WHEN am.campo_28_purchase_nd is not null THEN am.campo_28_purchase_nd
					ELSE 0
				END AS campo28,
				CASE
					WHEN am.campo_29_purchase_nd is not null THEN am.campo_29_purchase_nd
					ELSE 0
				END AS campo29,
				CASE
					WHEN am.campo_30_purchase_nd is not null THEN am.campo_30_purchase_nd
					ELSE 0
				END AS campo30,
				CASE
					WHEN rp1.c_d_imp is not null THEN rp1.c_d_imp
					ELSE NULL
				END AS campo31,
				CASE
					WHEN am.campo_32_purchase_nd is not null THEN am.campo_32_purchase_nd
					ELSE NULL
				END AS campo32,
				CASE
					WHEN am.campo_33_purchase_nd is not null THEN am.campo_33_purchase_nd
					ELSE NULL
				END AS campo33,
				CASE
					WHEN am.campo_34_purchase_nd is not null THEN am.campo_34_purchase_nd
					ELSE NULL
				END AS campo34,
				CASE
					WHEN am.campo_35_purchase_nd = TRUE THEN '1'
					ELSE NULL
				END AS campo35,
				CASE
					WHEN am.campo_41_purchase is not null THEN am.campo_41_purchase
					ELSE NULL
				END AS campo36,
				NULL AS campo47
				FROM vst_compras_1_1 vst_c
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp1 ON rp1.id = vst_c.partner_id
				LEFT JOIN res_partner rp2 ON rp2.id = am.campo_23_purchase_nd
				LEFT JOIN einvoice_catalog_01 ec01 ON ec01.id = am.campo_11_purchase_nd
				WHERE vst_c.td in ('00','91','97','98') and rp1.is_not_home = TRUE
				and (vst_c.fecha_cont between '%s' and '%s') and vst_c.company = %s
				ORDER BY vst_c.periodo, vst_c.libro, vst_c.voucher
				""" % (x_date_ini.strftime('%Y/%m/%d'),
			x_date_end.strftime('%Y/%m/%d'),
			str(x_company_id))

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