# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountBalanceDetailRep(models.TransientModel):
	_name = 'account.balance.detail.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')
	type_account = fields.Selection([('payable','Por Pagar'),('receivable','Por Cobrar'),('other','Otros')],string=u'Tipo')
	only_pending = fields.Boolean(string="Solo Pendientes",default=False)
	partner_id = fields.Many2one('res.partner',string=u'Partner')
	account_id = fields.Many2one('account.account',string=u'Cuenta')

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
		sql_partner = """"""
		sql_account = """"""
		sql_type_acc = """"""
		
		if self.only_pending:
			only_pendd = 1
		else:
			only_pendd = 0

		if self.partner_id:
			sql_partner = """and a1.partner_id = %s""" % (self.partner_id.id)
		if self.account_id:
			sql_account = """and a1.account_id = %s""" % (self.account_id.id)
		if self.type_account:
			sql_type_acc = """and a3.type = '%s'""" % (self.type_account)

		sql = """
			CREATE OR REPLACE view account_balance_detail_book as (SELECT row_number() OVER () AS id,a1.* FROM get_saldo_detalle('%s','%s',%s) a1 
			LEFT JOIN account_account a2 ON a2.id = a1.account_id
			LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
			WHERE concat(a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante) in(
			SELECT concat(partner_id,account_id,td_sunat,nro_comprobante) FROM get_saldos('%s','%s',%s,%s)) %s %s %s)""" % (
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				str(only_pendd),
				sql_partner,
				sql_account,
				sql_type_acc
			)

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Detalle Comprobantes',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.detail.book',
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

		workbook = Workbook(direccion +'Detalle_Comprobantes.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Detalle Comprobantes")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','NRO COMP','FEC DOC','FEC VEN','CUENTA','MONEDA','DEBE','HABER','BALANCE','IMPORTE ME','SALDO MN','SALDO ME']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, balance, importe_me = 0, 0, 0, 0

		for line in self.env['account.balance.detail.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,5,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,6,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,7,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,8,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,9,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,10,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,11,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,12,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,13,line.debe if line.debe else 0,formats['numberdos'])
			worksheet.write(x,14,line.haber if line.haber else 0,formats['numberdos'])
			worksheet.write(x,15,line.balance if line.balance else 0,formats['numberdos'])
			worksheet.write(x,16,line.importe_me if line.importe_me else 0,formats['numberdos'])
			worksheet.write(x,17,line.saldo if line.saldo else 0,formats['numberdos'])
			worksheet.write(x,18,line.saldo_me if line.saldo_me else 0,formats['numberdos'])
			x += 1
			debe += line.debe if line.debe else 0
			haber += line.haber if line.haber else 0
			balance += line.balance if line.balance else 0
			importe_me += line.importe_me if line.importe_me else 0

		worksheet.write(x,13,debe,formats['numbertotal'])
		worksheet.write(x,14,haber,formats['numbertotal'])
		worksheet.write(x,15,balance,formats['numbertotal'])
		worksheet.write(x,16,importe_me,formats['numbertotal'])

		widths = [7,10,10,10,4,11,40,4,10,10,10,10,10,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Detalle_Comprobantes.xlsx', 'rb')
		return self.env['popup.it'].get_file('Detalle Comprobantes.xlsx',base64.encodestring(b''.join(f.readlines())))

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