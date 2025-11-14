# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountEcpnRep(models.TransientModel):
	_name = 'account.ecpn.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period_id = fields.Many2one('account.period',string=u'Periodo',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		import io
		from xlsxwriter.workbook import Workbook
		from xlsxwriter.utility import xl_rowcol_to_cell
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'ecpn.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		formats['especial1'].set_border(style=0)
		formats['numberdos'].set_border(style=0)
		formats['especial2'].set_bg_color('#fef2cb')
		formats['numbertotal'].set_bg_color('#fef2cb')
		formats['numbertotal'].set_border(style=1)
		formats['numbertotal'].set_underline(0)
		formats['boldbord'].set_bg_color('#ffd965')

		subtitle = workbook.add_format({'bold': True})
		subtitle.set_align('center')
		subtitle.set_align('vcenter')
		subtitle.set_text_wrap()
		subtitle.set_font_size(10.5)
		subtitle.set_font_name('Times New Roman')

		worksheet = workbook.add_worksheet("ECPN")

		worksheet.write(0,0,self.company_id.name or '',subtitle)
		worksheet.write(1,0,'Estado de Cambio en el Patrimonio Neto' ,subtitle)
		worksheet.write(2,0,'Del Periodo de Apertura %s a %s'%(self.fiscal_year_id.name or '',self.period_id.name or '') ,subtitle)
		worksheet.write(3,0,'Expresado en: SOLES',subtitle)

		HEADERS = ['CUENTAS PATRIMONIALES']

		for i in self.env['account.patrimony.type'].search([]):
			HEADERS.append(i.name)
		HEADERS.append('TOTAL')

		worksheet = ReportBase.get_headers(worksheet,HEADERS,5,0,formats['boldbord'])
		
		x = 6

		self.env.cr.execute(self._get_sql())
		res = self.env.cr.dictfetchall()

		for line in res:
			worksheet.write(x,0,line['definicion'] if line['definicion'] else '(En Blanco)' ,formats['especial2'] if x==6 else formats['especial1'])
			j = 1
			for l in self.env['account.patrimony.type'].search([]):
				worksheet.write(x,j,line[l.code] if line[l.code] else 0,formats['numbertotal'] if x==6 else formats['numberdos'] )
				j +=1
			worksheet.write(x,j,line['total'] if line['total'] else 0,formats['numbertotal'] if x==6 else formats['numberdos'] )
			x += 1
		
		worksheet.write(x,0,'Saldos al %s'%(self.period_id.date_end.strftime('%Y/%m/%d')) ,formats['especial2'])
		j = 1
		for u in self.env['account.patrimony.type'].search([]):
			worksheet.write_formula(x,j, '=sum(' + xl_rowcol_to_cell(6,j) +':' +xl_rowcol_to_cell(x-1,j) + ')', formats['numbertotal'])
			j +=1
		worksheet.write_formula(x,j,'=sum(' + xl_rowcol_to_cell(6,j) +':' +xl_rowcol_to_cell(x-1,j) + ')',formats['numbertotal'])
		


		widths = [80,11,11,11,11,11,11,11,11,11]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'ecpn.xlsx', 'rb')
		return self.env['popup.it'].get_file('Patrimonio Neto.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self):
		sql_case = sql = ""

		for i in self.env['account.patrimony.type'].search([]):
			sql_case += """sum(
					CASE
						WHEN aa.patrimony_id = %d THEN coalesce(dg.balance,0) *-1
						ELSE 0
					END) AS "%s", \n"""%(i.id,i.code)

		
		for j in self.env['account.patrimony.table'].search([]):
			sql += """SELECT '%s' as definicion,
					%s
					sum(coalesce(dg.balance,0)) *-1 AS total
				FROM vst_diariog dg
				LEFT JOIN account_move am on am.id = dg.move_id
				LEFT JOIN account_move_line aml on aml.id = dg.move_line_id
				LEFT JOIN account_account aa on aa.id = dg.account_id
				LEFT JOIN account_patrimony_table apt2 on apt2.id = am.patrimony_table_id 
				WHERE (dg.fecha between '%s' AND '%s') and am.type in ('entry') AND am.patrimony_table_id = %d and aa.patrimony_id is not null
				AND dg.company_id = %d
				UNION ALL
				""" % (j.name,sql_case,self.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
					self.period_id.date_end.strftime('%Y/%m/%d'), j.id,
					self.company_id.id)

		return sql[:len(sql)-14]