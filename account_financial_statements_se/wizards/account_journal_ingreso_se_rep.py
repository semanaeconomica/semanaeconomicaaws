# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountJournalIngresoSeRep(models.TransientModel):
	_name = 'account.journal.ingreso.se.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla')],string=u'Mostrar en',default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):

		self.env.cr.execute("""
			DROP VIEW IF EXISTS account_journal_ingreso_se_book CASCADE;
			CREATE OR REPLACE view account_journal_ingreso_se_book as ("""+self._get_sql()+""")""")

		if self.type_show == 'pantalla':
			return {
				'name': 'Ingresos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.journal.ingreso.se.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'ingresos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		formats['especial1'].set_border(style=0)
		formats['numberdos'].set_border(style=0)

		subtitle = workbook.add_format({'bold': True})
		subtitle.set_align('justify')
		subtitle.set_align('vcenter')
		subtitle.set_text_wrap()
		subtitle.set_font_size(10)
		subtitle.set_bg_color('#DCE6F1')
		subtitle.set_font_name('Times New Roman')

		subtitlenumber = workbook.add_format({'bold': True,'num_format':'0.00'})
		subtitlenumber.set_align('right')
		subtitlenumber.set_align('vcenter')
		subtitlenumber.set_bg_color('#DCE6F1')
		subtitlenumber.set_font_size(10)
		subtitlenumber.set_font_name('Times New Roman')

		worksheet = workbook.add_worksheet("INGRESOS")

		HEADERS = ['ETIQUETAS DE FILA','01/%s'%(self.fiscal_year_id.name),'02/%s'%(self.fiscal_year_id.name),'03/%s'%(self.fiscal_year_id.name),'04/%s'%(self.fiscal_year_id.name),
		'05/%s'%(self.fiscal_year_id.name),'06/%s'%(self.fiscal_year_id.name),'07/%s'%(self.fiscal_year_id.name),'08/%s'%(self.fiscal_year_id.name),
		'09/%s'%(self.fiscal_year_id.name),'10/%s'%(self.fiscal_year_id.name),'11/%s'%(self.fiscal_year_id.name),'12/%s'%(self.fiscal_year_id.name),'TOTAL']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		
		x = 2

		worksheet.write(1,0,'CANJE',subtitle)

		self.env.cr.execute(self._get_sql_group_1())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['categoria'] if line['categoria'] else '(En Blanco)' ,formats['especial1'])
			worksheet.write(x,1,line['per01'] if line['per01']  else 0,formats['numberdos'])
			worksheet.write(x,2,line['per02'] if line['per02']  else 0,formats['numberdos'])
			worksheet.write(x,3,line['per03'] if line['per03']  else 0,formats['numberdos'])
			worksheet.write(x,4,line['per04'] if line['per04']  else 0,formats['numberdos'])
			worksheet.write(x,5,line['per05'] if line['per05']  else 0,formats['numberdos'])
			worksheet.write(x,6,line['per06'] if line['per06']  else 0,formats['numberdos'])
			worksheet.write(x,7,line['per07'] if line['per07']  else 0,formats['numberdos'])
			worksheet.write(x,8,line['per08'] if line['per08']  else 0,formats['numberdos'])
			worksheet.write(x,9,line['per09'] if line['per09']  else 0,formats['numberdos'])
			worksheet.write(x,10,line['per10'] if line['per10']  else 0,formats['numberdos'])
			worksheet.write(x,11,line['per11'] if line['per11']  else 0,formats['numberdos'])
			worksheet.write(x,12,line['per12'] if line['per12']  else 0,formats['numberdos'])
			worksheet.write(x,13,line['total'] if line['total']  else 0,formats['numberdos'])
			x += 1
		
		for i in range(1,14):
			worksheet.write_formula(1,i, '=sum(' + xl_rowcol_to_cell(2,i) +':' +xl_rowcol_to_cell(x-1,i) + ')', subtitlenumber)

		pos = x

		worksheet.write(pos,0,'EFECTIVO',subtitle)

		self.env.cr.execute(self._get_sql_group_2())
		res2 = self.env.cr.dictfetchall()

		x += 1

		for line in res2:
			worksheet.write(x,0,line['categoria'] if line['categoria'] else '(En Blanco)' ,formats['especial1'])
			worksheet.write(x,1,line['per01'] if line['per01']  else 0,formats['numberdos'])
			worksheet.write(x,2,line['per02'] if line['per02']  else 0,formats['numberdos'])
			worksheet.write(x,3,line['per03'] if line['per03']  else 0,formats['numberdos'])
			worksheet.write(x,4,line['per04'] if line['per04']  else 0,formats['numberdos'])
			worksheet.write(x,5,line['per05'] if line['per05']  else 0,formats['numberdos'])
			worksheet.write(x,6,line['per06'] if line['per06']  else 0,formats['numberdos'])
			worksheet.write(x,7,line['per07'] if line['per07']  else 0,formats['numberdos'])
			worksheet.write(x,8,line['per08'] if line['per08']  else 0,formats['numberdos'])
			worksheet.write(x,9,line['per09'] if line['per09']  else 0,formats['numberdos'])
			worksheet.write(x,10,line['per10'] if line['per10']  else 0,formats['numberdos'])
			worksheet.write(x,11,line['per11'] if line['per11']  else 0,formats['numberdos'])
			worksheet.write(x,12,line['per12'] if line['per12']  else 0,formats['numberdos'])
			worksheet.write(x,13,line['total'] if line['total']  else 0,formats['numberdos'])
			x += 1

		for i in range(1,14):
			worksheet.write_formula(pos,i, '=sum(' + xl_rowcol_to_cell(pos+1,i) +':' +xl_rowcol_to_cell(x-1,i) + ')', subtitlenumber)

		worksheet.write(x,0,'Total General',formats['especial2'])

		for i in range(1,14):
			worksheet.write_formula(x,i, '=' + xl_rowcol_to_cell(1,i) +'+' +xl_rowcol_to_cell(pos,i), formats['numbertotal'])


		widths = [20,10,10,10,10,10,10,10,10,10,10,10,10,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'ingresos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ingresos.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):

		sql = """SELECT row_number() OVER () AS id, T.* FROM (SELECT
				vst1.periodo,vst1.fecha,vst1.libro,vst1.voucher,
				vst1.cuenta,vst1.balance*-1 as balance,
				vst1.moneda,vst1.tc,vst1.importe_me,vst1.code_cta_analitica,
				vst1.glosa,vst1.td_partner,vst1.doc_partner,vst1.partner,
				vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
				ang.name as canje
				FROM vst_diariog vst1
				LEFT JOIN account_move_line aml on aml.id = vst1.move_line_id
				LEFT JOIN account_analytic_account ana on ana.id = aml.analytic_account_id
				LEFT JOIN account_analytic_group ang on ang.id = ana.group_id
				WHERE (vst1.fecha between '%s' AND '%s') and left(vst1.cuenta,2) = '70'
				AND vst1.company_id = %d)T
			""" % (self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
				self.company_id.id)

		return sql

	def _get_sql_group_1(self):

		sql = """SELECT PC.name as categoria,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '01' THEN dg.balance
						ELSE 0::numeric
					END) AS per01,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '02' THEN dg.balance
						ELSE 0::numeric
					END) AS per02,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '03' THEN dg.balance
						ELSE 0::numeric
					END) AS per03,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '04' THEN dg.balance
						ELSE 0::numeric
					END) AS per04,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '05' THEN dg.balance
						ELSE 0::numeric
					END) AS per05,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '06' THEN dg.balance
						ELSE 0::numeric
					END) AS per06,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '07' THEN dg.balance
						ELSE 0::numeric
					END) AS per07,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '08' THEN dg.balance
						ELSE 0::numeric
					END) AS per08,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '09' THEN dg.balance
						ELSE 0::numeric
					END) AS per09,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '10' THEN dg.balance
						ELSE 0::numeric
					END) AS per10,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '11' THEN dg.balance
						ELSE 0::numeric
					END) AS per11,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '12' THEN dg.balance
						ELSE 0::numeric
					END) AS per12,
				sum(
					CASE
						WHEN right(dg.periodo,2) in ('01','02','03','04','05','06','07','08','09','10','11','12') THEN dg.balance
						ELSE 0::numeric
					END) AS total
			FROM vst_diariog dg
			LEFT JOIN account_move am on am.id = dg.move_id
			LEFT JOIN account_move_line aml on aml.id = dg.move_line_id
			LEFT JOIN product_product PP ON PP.id = aml.product_id
			LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
			LEFT JOIN product_category PC on PT.categ_id = PC.id
			WHERE (dg.fecha between '%s' AND '%s') AND aml.product_id is not null AND am.canje_se = 'canje' and am.type in ('out_invoice','out_refund') and left(dg.cuenta,2) = '70'
			AND dg.company_id = %d
			GROUP BY PC.name;
			""" % (self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
				self.company_id.id)

		return sql

	def _get_sql_group_2(self):

		sql = """SELECT PC.name as categoria,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '01' THEN dg.balance
						ELSE 0::numeric
					END) AS per01,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '02' THEN dg.balance
						ELSE 0::numeric
					END) AS per02,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '03' THEN dg.balance
						ELSE 0::numeric
					END) AS per03,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '04' THEN dg.balance
						ELSE 0::numeric
					END) AS per04,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '05' THEN dg.balance
						ELSE 0::numeric
					END) AS per05,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '06' THEN dg.balance
						ELSE 0::numeric
					END) AS per06,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '07' THEN dg.balance
						ELSE 0::numeric
					END) AS per07,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '08' THEN dg.balance
						ELSE 0::numeric
					END) AS per08,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '09' THEN dg.balance
						ELSE 0::numeric
					END) AS per09,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '10' THEN dg.balance
						ELSE 0::numeric
					END) AS per10,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '11' THEN dg.balance
						ELSE 0::numeric
					END) AS per11,
				sum(
					CASE
						WHEN right(dg.periodo,2) = '12' THEN dg.balance
						ELSE 0::numeric
					END) AS per12,
				sum(
					CASE
						WHEN right(dg.periodo,2) in ('01','02','03','04','05','06','07','08','09','10','11','12') THEN dg.balance
						ELSE 0::numeric
					END) AS total
			FROM vst_diariog dg
			LEFT JOIN account_move am on am.id = dg.move_id
			LEFT JOIN account_move_line aml on aml.id = dg.move_line_id
			LEFT JOIN product_product PP ON PP.id = aml.product_id
			LEFT JOIN product_template PT ON PT.id = PP.product_tmpl_id
			LEFT JOIN product_category PC on PT.categ_id = PC.id
			WHERE (dg.fecha between '%s' AND '%s') AND aml.product_id is not null AND am.canje_se = 'cash' and am.type in ('out_invoice','out_refund') and left(dg.cuenta,2) = '70'
			AND dg.company_id = %d
			GROUP BY PC.name;
			""" % (self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.fiscal_year_id.date_to.strftime('%Y/%m/%d'),
				self.company_id.id)

		return sql