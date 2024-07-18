# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class WorksheetF2Wizard(models.TransientModel):
	_name = 'worksheet.f2.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],default='pantalla',string=u'Mostrar en', required=True)
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
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

	def _get_f2_register_sql(self):
		sql = """
		DROP VIEW IF EXISTS f2_register;
		CREATE OR REPLACE VIEW f2_register AS
		(
			SELECT row_number() OVER () AS id, 
			'{period}' as period,
			* FROM (
			SELECT *
			FROM get_f2_register('{period}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			null::character varying as cuenta,
			'SUMAS'::text as nomenclatura,
			sum(debe_inicial) as debe_inicial,
			sum(haber_inicial) as haber_inicial,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldo_deudor) as saldo_deudor,
			sum(saldo_acreedor) as saldo_acreedor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdinat) as perdinat,
			sum(ganannat) as ganannat,
			sum(perdifun) as perdifun,
			sum(gananfun) as gananfun,
			null::text as rubro
			FROM get_f2_register('{period}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			null::character varying as cuenta,
			'UTILIDAD O PERDIDA'::text as nomenclatura,
			case
				when sum(debe_inicial) < sum(haber_inicial)
				then sum(haber_inicial) - sum(debe_inicial)
				else 0
			end as debe_inicial,
			case
				when sum(debe_inicial) > sum(haber_inicial)
				then sum(debe_inicial) - sum(haber_inicial) 
				else 0
			end as haber_inicial,
			case
				when sum(debe) < sum(haber)
				then sum(haber) - sum(debe)
				else 0
			end as debe,
			case
				when sum(debe) > sum(haber)
				then sum(debe) - sum(haber) 
				else 0
			end as haber,
			case
				when sum(saldo_deudor) < sum(saldo_acreedor)
				then sum(saldo_acreedor) - sum(saldo_deudor)
				else 0
			end as saldo_deudor,
			case
				when sum(saldo_deudor) > sum(saldo_acreedor)
				then sum(saldo_deudor) - sum(saldo_acreedor)
				else 0
			end as saldo_acreedor,
			case
				when sum(activo) < sum(pasivo)
				then sum(pasivo) - sum(activo)
				else 0
			end as activo,
			case
				when sum(activo) > sum(pasivo)
				then sum(activo) - sum(pasivo)
				else 0
			end as pasivo,
			case
				when sum(perdinat) < sum(ganannat)
				then sum(ganannat) - sum(perdinat)
				else 0
			end as perdinat,
			case
				when sum(perdinat) > sum(ganannat)
				then sum(perdinat) - sum(ganannat)
				else 0
			end as ganannat,
			case
				when sum(perdifun) < sum(gananfun)
				then sum(gananfun) - sum(perdifun)
				else 0
			end as perdifun,
			case
				when sum(perdifun) > sum(gananfun)
				then sum(perdifun) - sum(gananfun)
				else 0
			end as gananfun,
			null::text as rubro
			FROM get_f2_register('{period}',{company},'{currency}')
				)T
		)
		""".format(
				period = self.period.code,
				company = self.company_id.id,
				currency = self.currency
			)
		print(sql)
		return sql

	def _get_f2_balance_sql(self):
		sql = """
		DROP VIEW IF EXISTS f2_balance;
		CREATE OR REPLACE VIEW f2_balance AS 
		(
			SELECT row_number() OVER () AS id,
			'{period}' as period,
			* FROM (
			SELECT *
			FROM get_f2_balance('{period}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			'SUMAS'::text as nomenclatura,
			sum(debe_inicial) as debe_inicial,
			sum(haber_inicial) as haber_inicial,
			sum(debe) as debe,
			sum(haber) as haber,
			sum(saldo_deudor) as saldo_deudor,
			sum(saldo_acreedor) as saldo_acreedor,
			sum(activo) as activo,
			sum(pasivo) as pasivo,
			sum(perdinat) as perdinat,
			sum(ganannat) as ganannat,
			sum(perdifun) as perdifun,
			sum(gananfun) as gananfun
			FROM get_f2_balance('{period}',{company},'{currency}')
			UNION ALL
			SELECT 
			null::text as mayor,
			'UTILIDAD O PERDIDA'::text as nomenclatura,
			case
				when sum(debe_inicial) < sum(haber_inicial)
				then sum(haber_inicial) - sum(debe_inicial)
				else 0
			end as debe_inicial,
			case
				when sum(debe_inicial) > sum(haber_inicial)
				then sum(debe_inicial) - sum(haber_inicial) 
				else 0
			end as haber_inicial,
			case
				when sum(debe) < sum(haber)
				then sum(haber) - sum(debe)
				else 0
			end as debe,
			case
				when sum(debe) > sum(haber)
				then sum(debe) - sum(haber) 
				else 0
			end as haber,
			case
				when sum(saldo_deudor) < sum(saldo_acreedor)
				then sum(saldo_acreedor) - sum(saldo_deudor)
				else 0
			end as saldo_deudor,
			case
				when sum(saldo_deudor) > sum(saldo_acreedor)
				then sum(saldo_deudor) - sum(saldo_acreedor)
				else 0
			end as saldo_acreedor,
			case
				when sum(activo) < sum(pasivo)
				then sum(pasivo) - sum(activo)
				else 0
			end as activo,
			case
				when sum(activo) > sum(pasivo)
				then sum(activo) - sum(pasivo)
				else 0
			end as pasivo,
			case
				when sum(perdinat) < sum(ganannat)
				then sum(ganannat) - sum(perdinat)
				else 0
			end as perdinat,
			case
				when sum(perdinat) > sum(ganannat)
				then sum(perdinat) - sum(ganannat)
				else 0
			end as ganannat,
			case
				when sum(perdifun) < sum(gananfun)
				then sum(gananfun) - sum(perdifun)
				else 0
			end as perdifun,
			case
				when sum(perdifun) > sum(gananfun)
				then sum(perdifun) - sum(gananfun)
				else 0
			end as gananfun
			FROM get_f2_balance('{period}',{company},'{currency}')
				)T
		)
		""".format(
				period = self.period.code,
				company = self.company_id.id,
				currency = self.currency
			)
		print(sql)
		return sql

	def get_report(self):
		self._cr.execute(self._get_f2_register_sql())
		if self.level == 'balance':
			self._cr.execute(self._get_f2_balance_sql())
		if self.type_show == 'pantalla':
			if self.level == 'register':
				return self.get_window_f2_register()
			else:
				return self.get_window_f2_balance()
		else:
			if self.level == 'register':
				return self.get_excel_f2_register()
			else:
				return self.get_excel_f2_balance()

	def get_window_f2_register(self):
		if self.show_account_entries:
			view = self.env.ref('account_htf2_report.view_f2_register_tree_true').id
		else:
			view = self.env.ref('account_htf2_report.view_f2_register_tree').id
		return {
			'name': 'Hoja de Trabajo F2 - Registro',
			'type': 'ir.actions.act_window',
			'res_model': 'f2.register',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_window_f2_balance(self):
		view = self.env.ref('account_htf2_report.view_f2_balance_tree').id
		return {
			'name': 'Hoja de Trabajo F2 - Balance',
			'type': 'ir.actions.act_window',
			'res_model': 'f2.balance',
			'view_mode': 'tree',
			'views': [(view, 'tree')],
		}

	def get_excel_f2_register(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F2.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F2")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','CUENTA','NOMENCLATURA','DEBE INICIAL','HABER INICIAL','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		if self.show_account_entries:
			HEADERS.append('RUBRO ESTADO FINANCIERO')
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		total = len(self.env['f2.register'].search([])) - 2
		for c,line in enumerate(self.env['f2.register'].search([]),1):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,2,line.nomenclatura if line.nomenclatura else '',formats['especial1'] if c <= total else formats['boldbord'])
			worksheet.write(x,3,line.debe_inicial if line.debe_inicial else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,4,line.haber_inicial if line.haber_inicial else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,5,line.debe if line.debe else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,6,line.haber if line.haber else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,7,line.saldo_deudor if line.saldo_deudor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,8,line.saldo_acreedor if line.saldo_acreedor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,9,line.activo if line.activo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,10,line.pasivo if line.pasivo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,11,line.perdinat if line.perdinat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,12,line.ganannat if line.ganannat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,13,line.perdifun if line.perdifun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,14,line.gananfun if line.gananfun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			if self.show_account_entries:
				worksheet.write(x,15,line.rubro if line.rubro else '',formats['especial1'])
			x += 1

		widths = [7,9,40,10,10,10,10,10,10,10,10,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F2.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja_Trabajo_F2_Nivel_Registro.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_f2_balance(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Hoja_Trabajo_F2.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Hoja de Trabajo F2")
		worksheet.set_tab_color('blue')

		HEADERS = ['MAYOR','NOMENCLATURA','DEBE INICIAL','HABER INICIAL','DEBE','HABER','SALDO DEUDOR','SALDO ACREEDOR',
				   'ACTIVO','PASIVO','PERDINAT','GANANNAT','PERDIFUN','GANANFUN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		total = len(self.env['f2.balance'].search([])) - 2
		for c,line in enumerate(self.env['f2.balance'].search([]),1):
			worksheet.write(x,0,line.mayor if line.mayor else '',formats['especial1'])
			worksheet.write(x,1,line.nomenclatura if line.nomenclatura else '',formats['especial1'] if c <= total else formats['boldbord'])
			worksheet.write(x,2,line.debe_inicial if line.debe_inicial else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,3,line.haber_inicial if line.haber_inicial else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,4,line.debe if line.debe else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,5,line.haber if line.haber else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,6,line.saldo_deudor if line.saldo_deudor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,7,line.saldo_acreedor if line.saldo_acreedor else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,8,line.activo if line.activo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,9,line.pasivo if line.pasivo else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,10,line.perdinat if line.perdinat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,11,line.ganannat if line.ganannat else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,12,line.perdifun if line.perdifun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			worksheet.write(x,13,line.gananfun if line.gananfun else 0,formats['numberdos'] if c <= total else formats['numbertotal'])
			x += 1

		widths = [7,40,10,10,10,10,10,10,10,10,10,10,10,10,40]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Hoja_Trabajo_F2.xlsx', 'rb')
		return self.env['popup.it'].get_file('Hoja_Trabajo_F2_Nivel_Balance.xlsx',base64.encodestring(b''.join(f.readlines())))