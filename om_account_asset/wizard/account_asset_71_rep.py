# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountAsset71Rep(models.TransientModel):
	_name = 'account.asset.71.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Año Fiscal',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],string=u'Mostrar en',default='pantalla')

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
				CREATE OR REPLACE view account_asset_71_book as ("""+self._get_sql_71(self.fiscal_year_id.date_from,self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
				
		if self.type_show == 'pantalla':
			return {
				'name': 'Formato 7.1',
				'type': 'ir.actions.act_window',
				'res_model': 'account.asset.71.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()
		
		if self.type_show == 'pdf':
			return self.getPdf()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Formato_71.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########FORMATO 7.1############
		worksheet = workbook.add_worksheet("FORMATO 7.1")
		worksheet.set_tab_color('blue')
		
		worksheet.merge_range(0,0,1,0, u"Código Relacionado con el Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,1,1,1, "Cuenta Contable del Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,2,0,5, u"Detalle del Activo Fijo",formats['boldbord'])
		HEADERS = [u'Descripción',u'Marca del Activo Fijo',u'Modelo del Activo Fijo',u'Número de Serie y/o Placa del Activo Fijo']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,1,2,formats['boldbord'])
		worksheet.merge_range(0,6,1,6, "Saldo Inicial",formats['boldbord'])
		worksheet.merge_range(0,7,1,7, "Adquisiones Adiciones",formats['boldbord'])
		worksheet.merge_range(0,8,1,8, "Mejoras",formats['boldbord'])
		worksheet.merge_range(0,9,1,9, "Retiros y/o Bajas",formats['boldbord'])
		worksheet.merge_range(0,10,1,10, "Otros Ajustes",formats['boldbord'])
		worksheet.merge_range(0,11,1,11, u"Valor Histórico del Activo Fijo al 31.12",formats['boldbord'])
		worksheet.merge_range(0,12,1,12, u"Ajuste por Inflación",formats['boldbord'])
		worksheet.merge_range(0,13,1,13, "Valor Ajustado del Activo Fijo al 31.12",formats['boldbord'])
		worksheet.merge_range(0,14,1,14, u"Fecha de Adquisición",formats['boldbord'])
		worksheet.merge_range(0,15,1,15, "Fecha Inicio del Uso del Activo Fijo",formats['boldbord'])
		worksheet.merge_range(0,16,0,17, u"Depreciación",formats['boldbord'])
		HEADERS = [u'Método Aplicado',u'Nro de Documento de Autorización']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,1,16,formats['boldbord'])
		worksheet.merge_range(0,18,1,18, u"Porcentaje de Depreciación",formats['boldbord'])
		worksheet.merge_range(0,19,1,19, u"Depreciación acumulada al Cierre del Ejercicio Anterior",formats['boldbord'])
		worksheet.merge_range(0,20,1,20, u"Depreciación del Ejercicio",formats['boldbord'])
		worksheet.merge_range(0,21,1,21, u"Depreciación del Ejercicio Relacionada con los retiros y/o bajas",formats['boldbord'])
		worksheet.merge_range(0,22,1,22, u"Depreciación relacionada con otros ajustes",formats['boldbord'])
		worksheet.merge_range(0,23,1,23, u"Depreciación acumulada Histórico",formats['boldbord'])
		worksheet.merge_range(0,24,1,24, u"Ajuste por inflación de la Depreciación",formats['boldbord'])
		worksheet.merge_range(0,25,1,25, u"Depreciación acumulada Ajustada por Inflación",formats['boldbord'])
		x=2

		for line in self.env['account.asset.71.book'].search([]):
			worksheet.write(x,0,line.campo1 if line.campo1 else '',formats['especial1'])
			worksheet.write(x,1,line.campo2 if line.campo2 else '',formats['especial1'])
			worksheet.write(x,2,line.campo3 if line.campo3 else '',formats['especial1'])
			worksheet.write(x,3,line.campo4 if line.campo4 else '',formats['especial1'])
			worksheet.write(x,4,line.campo5 if line.campo5 else '',formats['especial1'])
			worksheet.write(x,5,line.campo6 if line.campo6 else '',formats['especial1'])
			worksheet.write(x,6,line.campo7 if line.campo7 else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.campo8 if line.campo8 else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.campo9 if line.campo9 else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.campo10 if line.campo10 else '0.00',formats['numberdos'])
			worksheet.write(x,10,line.campo11 if line.campo11 else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.campo12 if line.campo12 else '0.00',formats['numberdos'])
			worksheet.write(x,12,line.campo13 if line.campo13 else '0.00',formats['numberdos'])
			worksheet.write(x,13,line.campo14 if line.campo14 else '0.00',formats['numberdos'])
			worksheet.write(x,14,line.campo15 if line.campo15 else '',formats['dateformat'])
			worksheet.write(x,15,line.campo16 if line.campo16 else '',formats['dateformat'])
			worksheet.write(x,16,line.campo17 if line.campo17 else '',formats['especial1'])
			worksheet.write(x,17,line.campo18 if line.campo18 else '',formats['especial1'])
			worksheet.write(x,18,line.campo19 if line.campo19 else '0.00',formats['numberdos'])
			worksheet.write(x,19,line.campo20 if line.campo20 else '0.00',formats['numberdos'])
			worksheet.write(x,20,line.campo21 if line.campo21 else '0.00',formats['numberdos'])
			worksheet.write(x,21,line.campo22 if line.campo22 else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.campo23 if line.campo23 else '0.00',formats['numberdos'])
			worksheet.write(x,23,line.campo24 if line.campo24 else '0.00',formats['numberdos'])
			worksheet.write(x,24,line.campo25 if line.campo25 else '0.00',formats['numberdos'])
			worksheet.write(x,25,line.campo26 if line.campo26 else '0.00',formats['numberdos'])
			
			x += 1

		widths = [14,14,55,25,15,14,13,13,13,13,13,13,13,13,12,12,14,17,20,18,13,18,13,13,13,13]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Formato_71.xlsx', 'rb')

		return self.env['popup.it'].get_file('Formato_71.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getPdf(self):
		raise UserError("Aun no esta disponible este formato.")

	def _get_sql_71(self,date_fiscal_year_start,date_period_start,date_period_end,company_id):
		sql = """
				select row_number() OVER () AS id,
				T.campo1,
				T.campo2,
				T.campo3,
				T.campo4,
				T.campo5,
				T.campo6,
				T.campo7,
				T.campo8,
				T.campo9,
				T.campo10,
				T.campo11,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11) as campo12,
				T.campo13,
				(T.campo7+T.campo8+T.campo9+T.campo10+T.campo11+T.campo13) as campo14,
				T.campo15,
				T.campo16,
				T.campo17,
				T.campo18,
				T.campo19,
				T.campo20,
				T.campo21,
				T.campo22,
				T.campo23,
				(T.campo20+T.campo21+T.campo22+T.campo23) as campo24,
				T.campo25,
				(T.campo20+T.campo21+T.campo22+T.campo23+T.campo25) as campo26
				from
				(select asset.code as campo1,
				aa.code as campo2,
				asset.name as campo3,
				asset.brand as campo4,
				asset.model as campo5,
				asset.plaque as campo6,
				case
					when asset.date < '%s' then asset.value
					else 0
				end
				as campo7,
				case
					when asset.date >= '%s' then asset.value
					else 0
				end
				as campo8,
				0 as campo9,
				0 as campo10,
				0 as campo11,
				0 as campo13,
				asset.date as campo15,
				asset.first_depreciation_manual_date as campo16,
				'Metodo Lineal' as campo17,
				asset.depreciation_authorization as campo18,
				asset.depreciation_rate as campo19,
				case 
				when t1.campo20 is not null then t1.campo20
				else 0
				end
				as campo20,
				case 
				when t2.campo21 is not null then t2.campo21
				else 0
				end
				as campo21,
				0 as campo22,
				0 as campo23,
				0 as campo25,
				asset.id as asset_id
				from account_asset_asset asset
				left join account_asset_category cat on cat.id = asset.category_id
				left join account_account aa on aa.id = cat.account_asset_id
				left join (select asset_id, sum(amount) as campo20 from account_asset_depreciation_line 
				where depreciation_date < '%s'
				group by asset_id)t1 on t1.asset_id = asset.id
				left join (select asset_id, sum(amount) as campo21 from account_asset_depreciation_line 
				where (depreciation_date between '%s' and '%s')
				group by asset_id)t2 on t2.asset_id = asset.id
				where asset.company_id = %d and (asset.only_format_74 = False or asset.only_format_74 is null) and asset.state <> 'draft'
				and asset.date < '%s' and (asset.f_baja is null or asset.f_baja > '%s'))T
		""" % (date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_fiscal_year_start.strftime('%Y/%m/%d'),
		date_period_end.strftime('%Y/%m/%d'),
		company_id,
		date_period_end.strftime('%Y/%m/%d'),
		date_period_start.strftime('%Y/%m/%d'))

		return sql