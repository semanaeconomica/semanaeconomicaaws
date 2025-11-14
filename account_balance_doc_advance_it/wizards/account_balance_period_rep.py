# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table
from reportlab.lib.units import  cm,mm
from reportlab.lib.utils import simpleSplit

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import time
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import *

class AccountBalancePeriodRep(models.TransientModel):
	_inherit = 'account.balance.period.rep'

	def get_report(self):
		self.domain_dates()
		if not self.only_pending:
			sql_type = 0
		else:
			sql_type = 1
		
		sql_type_account = """"""
		sql_partner = """"""
		sql_account = """"""

		if self.partner_id:
			sql_partner = """and a1.partner_id = %s""" % (self.partner_id.id)
		if self.account_id:
			sql_account = """and a1.account_id = %s""" % (self.account_id.id)
		if self.type_account:
			sql_type_account = """and a3.type = '%s'""" % (self.type_account)

		sql = """
			CREATE OR REPLACE view account_balance_period_book as (SELECT a1.*, CASE WHEN aml.expected_pay_date IS NOT NULL THEN aml.expected_pay_date ELSE a1.fecha_ven END AS expected_pay_date FROM get_saldos('%s','%s',%s,%s) a1
				LEFT JOIN account_move_line aml on aml.id = a1.move_line_id
				LEFT JOIN account_account a2 ON a2.id = a1.account_id
				LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
				WHERE a1.id is not null %s %s %s)""" % (
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				str(sql_type),
				sql_type_account,
				sql_partner,
				sql_account
			)

		self.env.cr.execute(sql)
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Saldo por Fecha Contable',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.period.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

		if self.type_show == 'pdf':
			return self.get_pdf()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Saldo_por_Fecha_Cont.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Saldo por Fecha Contable")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FEC CON','LIBRO','VOUCHER','TDP','RUC','PARTNER','TD','NRO COMP','FEC DOC','FEC VEN','FEC PREVISTA PAGO','CUENTA', 'MONEDA','DEBE','HABER','SALDO MN','SALDO ME']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, saldo_mn, saldo_me = 0, 0, 0, 0

		for line in self.env['account.balance.period.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha_con if line.fecha_con else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,5,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,6,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,7,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,8,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,9,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,10,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,11,line.expected_pay_date if line.expected_pay_date else '',formats['dateformat'])
			worksheet.write(x,12,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,13,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,14,line.debe if line.debe else 0,formats['numberdos'])
			worksheet.write(x,15,line.haber if line.haber else 0,formats['numberdos'])
			worksheet.write(x,16,line.saldo_mn if line.saldo_mn else 0,formats['numberdos'])
			worksheet.write(x,17,line.saldo_me if line.saldo_me else 0,formats['numberdos'])
			x += 1
			debe += line.debe if line.debe else 0
			haber += line.haber if line.haber else 0
			saldo_mn += line.saldo_mn if line.saldo_mn else 0
			saldo_me += line.saldo_me if line.saldo_me else 0

		worksheet.write(x,14,debe,formats['numbertotal'])
		worksheet.write(x,15,haber,formats['numbertotal'])
		worksheet.write(x,16,saldo_mn,formats['numbertotal'])
		worksheet.write(x,17,saldo_me,formats['numbertotal'])

		widths = [7,10,10,10,4,11,40,4,10,10,10,10,10,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Saldo_por_Fecha_Cont.xlsx', 'rb')
		return self.env['popup.it'].get_file('Saldo por Fecha Contable.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_pdf(self):
		#CREANDO ARCHIVO PDF
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		name_file = "Saldo_por_Fecha_Cont.pdf"
	
		archivo_pdf = SimpleDocTemplate(str(direccion)+name_file, pagesize=(2200,1000), rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)

		elements = []
		#Estilos 
		style_title = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 40, fontName="Times-Roman" )
		style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY , fontSize = 24, fontName="Times-Roman" )
		style_cell = ParagraphStyle(name = 'Center',alignment = TA_CENTER, fontSize = 12, fontName="Times-Roman" )
		

		company = self.company_id
		texto = "Reporte Saldo por Periodo"		
		elements.append(Paragraph(texto, style_title))
		elements.append(Spacer(1, 60))
		texto = 'Empresa: ' + (company.name)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Dirección: ' + (company.street)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Ruc: ' + (company.vat)
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 12))
		texto = 'Rango Fecha: ' + str(self.date_ini) + ' - ' + str(self.date_end)
		elements.append(Paragraph(texto,style_form))
		elements.append(Spacer(1, 12))
		texto = 'Fecha de Reporte: ' + str(date.today()) 
		elements.append(Paragraph(texto, style_form))
		elements.append(Spacer(1, 80))


	#Crear Tabla
		data = [[
			'Periodo',
			'Fecha',
			'Libro',
			'Voucher',
			'TDP',
			'RUC',
			'Partner',
			'TD',
			'Nro_Comp',			
			'Fecha Doc',
			'Fecha Ven',
			'Fecha Prev. Pago',
			'Cuenta',
			'Moneda',
			'Debe',
			'Haber',
			'Saldo Mn',
			'Saldo Me'
		]]	

		totales = [0,0,0,0]
		for fila in self.env['account.balance.period.book'].search([]):
			periodo = (fila['periodo']) if fila['periodo'] else ''
			fecha = str(fila['fecha_con']) if fila['fecha_con'] else ''
			libro = (fila['libro']) if fila['libro'] else ''
			voucher = (fila['voucher']) if fila['voucher'] else ''
			td_partner = (fila['td_partner']) if fila['td_partner'] else ''
			doc_partner = (fila['doc_partner']) if fila['doc_partner'] else ''
			partner = (fila['partner']) if fila['partner'] else ''
			td_sunat = (fila['td_sunat']) if fila['td_sunat'] else ''
			nro_comprobante = (fila['nro_comprobante']) if fila['nro_comprobante'] else ''
			fecha_doc = str(fila['fecha_doc']) if fila['fecha_doc'] else ''
			fecha_ven = str(fila['fecha_ven']) if fila['fecha_ven'] else ''
			fecha_prev = str(fila['expected_pay_date']) if fila['expected_pay_date'] else ''
			cuenta = (fila['cuenta']) if fila['cuenta'] else ''
			moneda = (fila['moneda']) if fila['moneda'] else ''
			debe = (fila['debe']) if fila['debe'] else 0.00
			haber = (fila['haber']) if fila['haber'] else 0.00
			saldo_mn = (fila['saldo_mn']) if fila['saldo_mn'] else 0.00
			saldo_me = (fila['saldo_me']) if fila['saldo_me'] else 0.00

			totales[0] += debe
			totales[1] += haber
			totales[2] += saldo_mn
			totales[3] += saldo_me
 
			data.append([
					periodo,
					fecha,
					libro ,
					voucher,
					td_partner,
					doc_partner,
					partner,
					td_sunat,
					nro_comprobante,
					fecha_doc,
					fecha_ven,
					fecha_prev,
					cuenta,
					moneda,
					str(debe),
					str(haber),
					str(saldo_mn),
					str(saldo_me)
				])
		data.append([
			'Totales',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			'',
			str(totales[0]),
			str(totales[1]),
			str(totales[2]),
			str(totales[3])
			])

	#Estilo de Tabla
		style = TableStyle([
			('ALIGN',(1,1),(-2,-2),'RIGHT'),					   
		   ('VALIGN',(0,0),(0,-1),'TOP'),					   
		   ('ALIGN',(0,-1),(-1,-1),'CENTER'),
		   ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),					   
		   ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
		   ('BOX', (0,0), (-1,-1), 0.25, colors.black)
	  	])		
	#Configure style and word wrap

		data2 = [[Paragraph(cell, style_cell) for cell in row] for row in data]

		pdftable=Table(data2)
		pdftable.setStyle(style)		 
		elements.append(pdftable)

	#Build
		archivo_pdf.build(elements)

		#Caracteres Especiales
		import importlib
		import sys
		importlib.reload(sys)
		import os


		f = open(str(direccion) + name_file, 'rb')		

		return self.env['popup.it'].get_file('Saldo por Fecha Contable.pdf',base64.encodestring(b''.join(f.readlines())))