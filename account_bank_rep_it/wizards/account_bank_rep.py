# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountBankRep(models.TransientModel):
	_name = 'account.bank.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	account_id = fields.Many2one('account.account',string='Cuenta')
	period_start = fields.Many2one('account.period',string='Periodo Inicial')
	period_end = fields.Many2one('account.period',string='Periodo Final')
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en',default='excel')

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

		self.env.cr.execute("""
			CREATE OR REPLACE view account_bank_book as ("""+self._get_sql(self.period_start.code,self.period_end.code,self.account_id.code,self.company_id.id)+""")""")

		if self.type_show == 'pantalla':
			return {
				'name': 'Auxiliar Bancos',
				'type': 'ir.actions.act_window',
				'res_model': 'account.bank.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
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

		workbook = Workbook(direccion +'AuxiliarBancos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########AUXILIAR DE BANCOS############
		worksheet = workbook.add_worksheet("AUXILIAR DE BANCOS")
		worksheet.set_tab_color('blue')

		worksheet.write(0,0, self.company_id.partner_id.name, formats['especial2'])
		worksheet.write(1,0, self.company_id.partner_id.vat, formats['especial2'])
		worksheet.merge_range(2,0,2,12, "LIBRO AUXILIAR DE CAJA Y BANCOS", formats['especial5'] )
		worksheet.merge_range(3,0,3,12, "(DEL "+ str(self.period_start.date_start) +" AL " + str(self.period_end.date_end) +")", formats['especial5'])

		worksheet.write(5,0,"Cuenta Bancaria/Caja:",formats['especial2'])
		worksheet.write(5,2,self.account_id.name,formats['especial2'])
		worksheet.write(6,0,"Moneda:",formats['especial2'])
		worksheet.write(6,2,self.account_id.currency_id.name if self.account_id.currency_id.name else '',formats['especial2'])

		HEADERS = ['Fecha','Nombre/Razón Social','Documento','Glosa','Cargo MN','Abono MN','Saldo MN','Cargo ME','Abono ME','Saldo ME','Nro. De Asiento']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,7,0,formats['boldbord'])
		x = 8

		for line in self.env['account.bank.book'].search([]):
			worksheet.write(x,0,line.fecha if line.fecha else '' ,formats['dateformat'] )
			worksheet.write(x,1,line.partner if line.partner  else '',formats['especial1'] )
			worksheet.write(x,2,line.documento if line.documento  else '',formats['especial1'])
			worksheet.write(x,3,line.glosa if line.glosa  else '',formats['especial1'])
			worksheet.write(x,4,line.cargomn ,formats['numberdos'])
			worksheet.write(x,5,line.abonomn ,formats['numberdos'])
			worksheet.write(x,6,line.saldomn ,formats['numberdos'])

			worksheet.write(x,7,line.cargome ,formats['numberdos'])
			worksheet.write(x,8,line.abonome ,formats['numberdos'])
			worksheet.write(x,9,line.saldome ,formats['numberdos'])

			worksheet.write(x,10,line.asiento if line.asiento else '' ,formats['especial1'])

			x += 1

		worksheet.write(x,2, 'TOTAL', formats['especial1'])
		worksheet.write_formula(x,4, '=sum(' + xl_rowcol_to_cell(8,4) +':' +xl_rowcol_to_cell(x-1,4) + ')', formats['numberdos'])
		worksheet.write_formula(x,5, '=sum(' + xl_rowcol_to_cell(8,5) +':' +xl_rowcol_to_cell(x-1,5) + ')', formats['numberdos'])
		worksheet.write_formula(x,7, '=sum(' + xl_rowcol_to_cell(8,7) +':' +xl_rowcol_to_cell(x-1,7) + ')', formats['numberdos'])
		worksheet.write_formula(x,8, '=sum(' + xl_rowcol_to_cell(8,8) +':' +xl_rowcol_to_cell(x-1,8) + ')', formats['numberdos'])

		widths = [14,24,14,36,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'AuxiliarBancos.xlsx', 'rb')
		return self.env['popup.it'].get_file('AuxiliarBancos.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self,period_start,period_end,cuenta,company_id):

		if int(period_start[4:]) > int(period_end[4:]):
			raise UserError('EL PERIODO FINAL SIEMPRE TIENE QUE SER  MAYOR O IGUAL QUE EL PERIODO INICIAL')

		periodo1 = period_start[:4] + '00'
		periodo2 = period_start[:4] + str('{:02d}'.format(int(period_start[4:])-1))

		sql = """
		SELECT 
		row_number() OVER () AS id,
		fecha,partner,documento,glosa,cargo AS cargomn,abono AS abonomn,
		(
			SELECT SUM(cargo-abono)
			FROM get_auxiliar_bancos(%s,%s,%s,%s,'%s',%s) AS b
			WHERE b.id<=a.id
		) AS saldomn,
		CASE WHEN importedivisa > 0 THEN importedivisa ELSE 0 END AS cargome,
		CASE WHEN importedivisa < 0 THEN ABS(importedivisa) ELSE 0 END AS abonome,
		(
			SELECT SUM(importedivisa)
			FROM get_auxiliar_bancos(%s,%s,%s,%s,'%s',%s) AS b
			WHERE b.id<=a.id
		) AS saldome,
		asiento
		FROM get_auxiliar_bancos(%s,%s,%s,%s,'%s',%s) a

		""" % (periodo1,periodo2,period_start,period_end,cuenta,str(company_id),
		periodo1,periodo2,period_start,period_end,cuenta,str(company_id),
		periodo1,periodo2,period_start,period_end,cuenta,str(company_id))

		return sql