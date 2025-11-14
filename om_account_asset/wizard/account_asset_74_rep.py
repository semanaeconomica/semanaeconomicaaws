# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
import time

class AccountAsset74Rep(models.TransientModel):
	_name = 'account.asset.74.rep'

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
				CREATE OR REPLACE view account_asset_74_book as ("""+self._get_sql_74(self.period.date_start,self.period.date_end,self.company_id.id)+""")""")
				
		if self.type_show == 'pantalla':
			return {
				'name': 'Formato 7.4',
				'type': 'ir.actions.act_window',
				'res_model': 'account.asset.74.book',
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

		workbook = Workbook(direccion +'Formato_74.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########FORMATO 7.4############
		worksheet = workbook.add_worksheet("FORMATO 7.4")
		worksheet.set_tab_color('blue')

		HEADERS = [u'ACTIVO FIJO',u'FECHA DEL CONTRATO','NUMERO DEL CONTRATO DE ARRENDAMIENTO','FECHA DE INICIO DEL CONTRATO','NUMERO DE CUOTAS PACTADAS','MONTO DEL CONTRATO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.asset.74.book'].search([]):
			worksheet.write(x,0,line.campo1 if line.campo1 else '',formats['especial1'])
			worksheet.write(x,1,line.campo2 if line.campo2 else '',formats['dateformat'])
			worksheet.write(x,2,line.campo3 if line.campo3 else '',formats['especial1'])
			worksheet.write(x,3,line.campo4 if line.campo4 else '',formats['dateformat'])
			worksheet.write(x,4,line.campo5 if line.campo5 else '0',formats['number'])
			worksheet.write(x,5,line.campo6 if line.campo6 else '0.00',formats['numberdos'])
			x += 1

		widths = [50,20,20,14,12,11]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Formato_74.xlsx', 'rb')

		return self.env['popup.it'].get_file('Formato_74.xlsx',base64.encodestring(b''.join(f.readlines())))

	def getPdf(self):
		#CREANDO ARCHIVO PDF
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Formato_74.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(800,450), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 24, fontName="Helvetica" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 12, fontName="Helvetica" )
		style_left = ParagraphStyle(name = 'Left', alignment=TA_LEFT, fontSize=9, fontName="Helvetica")
		style_right = ParagraphStyle(name = 'Right', alignment=TA_RIGHT, fontSize=9, fontName="Helvetica")
		style_title_tab = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 9, fontName="Helvetica-Bold" )
		

		company = self.company_id
		texto = "Formato 7.4"		
		elements.append(Paragraph(texto, style_title))
		elements.append(Spacer(1, 30))
		texto = 'Empresa: ' + (company.name)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Dirección: ' + (company.street if company.street else '')
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Ruc: ' + (company.vat if company.vat else '')
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Fecha de Reporte: ' + str(date.today()) 
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 30))


	#Crear Tabla
		HEADERS = [u'ACTIVO FIJO',u'FECHA DEL CONTRATO','NUMERO DEL CONTRATO DE ARRENDAMIENTO','FECHA DE INICIO DEL CONTRATO','NUMERO DE CUOTAS PACTADAS','MONTO DEL CONTRATO']

		datos = []
		datos.append([])

		for i in HEADERS:
			datos[0].append(Paragraph(i,style_title_tab))

		for c,fila in enumerate(self.env['account.asset.74.book'].search([])):
			datos.append([])
			datos[c+1].append(Paragraph((fila['campo1']) if fila['campo1'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['campo2']) if fila['campo2'] else '',style_left))
			datos[c+1].append(Paragraph((fila['campo3']) if fila['campo3'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['campo4']) if fila['campo4'] else '',style_left))
			datos[c+1].append(Paragraph(str(fila['campo5']) if fila['campo5'] else '0',style_right))
			datos[c+1].append(Paragraph(str(fila['campo6']) if fila['campo6'] else '0.00',style_right))

		table_datos = Table(datos, colWidths=[11.5*cm,2.7*cm,3.5*cm,2.7*cm,2.6*cm,2.7*cm])

		color_cab = colors.Color(red=(220/255),green=(230/255),blue=(241/255))

		#Estilo de Tabla
		style_table = TableStyle([
				('BACKGROUND', (0, 0), (26, 0),color_cab),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('GRID', (0,0), (-1,-1), 0.25, colors.black), 
				('BOX', (0,0), (-1,-1), 0.25, colors.black),
			])
		table_datos.setStyle(style_table)

		elements.append(table_datos)

		#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file(name_file,base64.encodestring(b''.join(f.readlines())))

	def _get_sql_74(self,date_period_start,date_period_end,company_id):
		sql = """select row_number() OVER () AS id,
				name as campo1, 
				contract_date as campo2, 
				contract_number as campo3,
				date_start_contract as campo4,
				fees_number as campo5, 
				amount_total_contract as campo6 
				from account_asset_asset
				where company_id = %d and contract_date <= '%s' and contract_date is not null and state <> 'draft'
				and (f_baja is null or f_baja > '%s')
				""" % (company_id,date_period_end.strftime('%Y/%m/%d'),date_period_start.strftime('%Y/%m/%d'))

		return sql