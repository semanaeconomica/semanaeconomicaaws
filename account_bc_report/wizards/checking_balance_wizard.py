# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class CheckingBalanceWizard(models.TransientModel):
	_name = 'checking.balance.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)
	show_account_entries = fields.Boolean(string='Mostrar Rubros de Cuenta',default=False)
	level = fields.Selection([('balance','Balance'),('register','Registro')],default='balance',string='Nivel',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def _get_register_sql(self):
		sql = """
		CREATE OR REPLACE VIEW checking_register AS 
		(
			SELECT row_number() OVER () AS id, T.mayor, T.cuenta, T.nomenclatura, T.debe, T.haber, T.saldo_deudor, T.saldo_acreedor, T.rubro
			FROM get_f1_register('%s','%s',%d,'pen') T
		)
		""" % (self.period_from.code,self.period_to.code,self.company_id.id)
		return sql

	def _get_balance_sql(self):
		sql = """
		CREATE OR REPLACE VIEW checking_balance AS 
		(
			SELECT row_number() OVER () AS id, T.mayor,T.nomenclatura, T.debe, T.haber, T.saldo_deudor, T.saldo_acreedor
			FROM get_f1_balance('%s','%s',%d,'pen')T
		)
		""" % (self.period_from.code,self.period_to.code,self.company_id.id)
		return sql

	def get_report(self):
		self._cr.execute(self._get_register_sql())
		if self.level == 'balance':
			self._cr.execute(self._get_balance_sql())
		if self.type_show == 'pantalla':
			if self.level == 'register':
				return self.get_window_checking_register()
			else:
				return self.get_window_checking_balance()
		else:
			if self.level == 'register':
				return self.get_excel_checking_register()
			else:
				return self.get_excel_checking_balance()

	def get_window_checking_register(self):
		if self.show_account_entries:
			view = self.env.ref('account_bc_report.view_checking_register_tree_true').id
		else:
			view = self.env.ref('account_bc_report.view_checking_register_tree').id
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'checking.register',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_window_checking_balance(self):
		view = self.env.ref('account_bc_report.view_checking_balance_tree').id
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'checking.balance',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_excel_checking_register(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Balance_Comprobacion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Balance Comprobacion")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','CUENTA','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR']
		if self.show_account_entries:
			HEADERS.append('RUBRO ESTADO FINANCIERO')
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, saldo_deudor, saldo_acreedor = 0, 0, 0, 0

		for line in self.env['checking.register'].search([]):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.nomenclatura if line.nomenclatura else '',formats['especial1'])
			worksheet.write(x,3,line.debe if line.debe else '',formats['numberdos'])
			worksheet.write(x,4,line.haber if line.haber else '',formats['numberdos'])
			worksheet.write(x,5,line.saldo_deudor if line.saldo_deudor else '',formats['numberdos'])
			worksheet.write(x,6,line.saldo_acreedor if line.saldo_acreedor else '',formats['numberdos'])
			if self.show_account_entries:
				worksheet.write(x,7,line.rubro if line.rubro else '',formats['especial1'])
			x += 1
			debe += line.debe if line.debe else 0
			haber += line.haber if line.haber else 0
			saldo_deudor += line.saldo_deudor if line.saldo_deudor else 0
			saldo_acreedor += line.saldo_acreedor if line.saldo_acreedor else 0

		worksheet.write(x,3,debe,formats['numbertotal'])
		worksheet.write(x,4,haber,formats['numbertotal'])
		worksheet.write(x,5,saldo_deudor,formats['numbertotal'])
		worksheet.write(x,6,saldo_acreedor,formats['numbertotal'])

		widths = [7,9,40,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Balance_Comprobacion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Balance_Comprobacion_Nivel_Registro.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_checking_balance(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Balance_Comprobacion.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Balance Comprobacion")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','NOMENCLATURA','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, saldo_deudor, saldo_acreedor = 0, 0, 0, 0

		for line in self.env['checking.balance'].search([]):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.nomenclatura if line.nomenclatura else '',formats['especial1'])
			worksheet.write(x,2,line.debe if line.debe else 0,formats['numberdos'])
			worksheet.write(x,3,line.haber if line.haber else 0,formats['numberdos'])
			worksheet.write(x,4,line.saldo_deudor if line.saldo_deudor else 0,formats['numberdos'])
			worksheet.write(x,5,line.saldo_acreedor if line.saldo_acreedor else 0,formats['numberdos'])
			x += 1
			debe += line.debe if line.debe else 0
			haber += line.haber if line.haber else 0
			saldo_deudor += line.saldo_deudor if line.saldo_deudor else 0
			saldo_acreedor += line.saldo_acreedor if line.saldo_acreedor else 0

		worksheet.write(x,2,debe,formats['numbertotal'])
		worksheet.write(x,3,haber,formats['numbertotal'])
		worksheet.write(x,4,saldo_deudor,formats['numbertotal'])
		worksheet.write(x,5,saldo_acreedor,formats['numbertotal'])

		widths = [7,40,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Balance_Comprobacion.xlsx', 'rb')
		return self.env['popup.it'].get_file('Balance_Comprobacion_Nivel_Balance.xlsx',base64.encodestring(b''.join(f.readlines())))