# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class FinancialSituationWizard(models.TransientModel):
	_name = 'financial.situation.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_from = fields.Many2one('account.period',string='Periodo Inicial',required=True)
	period_to = fields.Many2one('account.period',string='Periodo Final',required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel'),('pdf','PDF')],default='pantalla',string=u'Mostrar en', required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def _get_financial_situation_sql(self):
		sql = """
		CREATE OR REPLACE VIEW financial_situation AS 
		(
			SELECT row_number() OVER () AS id,
			at.name,
			at.group_balance,
			case
				when at.group_balance in ('B1','B2')
				then sum(debe) - sum(haber)
				else sum(haber) - sum(debe)
			end as total,
			at.order_balance
			from get_bc_register('{period_from}','{period_to}',{company}) bcr
			left join account_account aa on aa.code = bcr.cuenta and aa.company_id = {company}
			left join account_type_it at on at.id = aa.account_type_it_id
			where group_balance is not null
			group by at.name,at.group_balance,at.order_balance
			order by at.order_balance
		)
		""".format(
				period_from = self.period_from.code,
				period_to = self.period_to.code,
				company = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_financial_situation_sql())
		if self.type_show == 'pantalla':
			return self.get_window_financial_situation()
		elif self.type_show == 'pdf':
			return self.get_pdf_financial_situation()
		else:
			return self.get_excel_financial_situation()

	def delete_childs(self,groups):
		form_view = self.env['ir.model.data'].xmlid_to_object('account_balance_rep_it.view_dynamic_financial_situation_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))
		for group in groups:
			xml_group = xml_form.xpath("//group[@id='%s']" % group['xml_group'])[0]
			for child in xml_group:
				child.getparent().remove(child)
		xml_group = xml_form.xpath("//group[@id='resultado_periodo']")[0]
		for child in xml_group:
			child.getparent().remove(child)
		xml_group = xml_form.xpath("//group[@id='total_activo']")[0]
		for child in xml_group:
			child.getparent().remove(child)
		xml_group = xml_form.xpath("//group[@id='total_pasivo']")[0]
		for child in xml_group:
			child.getparent().remove(child)
		form_view.write({'arch': etree.tostring(xml_form)})

	def generate_fields(self,xml_form,groups,DynamicModel):
		for group in groups:
			currents = self.env['financial.situation'].search([('group_balance','=',group['balance_group'])])
			for c,current in enumerate(currents):
				self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_%s_%s' % (c, group['balance_group']),
						'field_description': current.name,
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
				xml_group = xml_form.xpath("//group[@id='%s']" % group['xml_group'])[0]
				etree.SubElement(xml_group, "field", name = 'x_%s_%s' % (c, group['balance_group']))
			self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_total_%s' % group['balance_group'],
						'field_description': group['total'],
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
			xml_group = xml_form.xpath("//group[@id='%s']" % group['xml_group'])[0]
			etree.SubElement(xml_group, "field", name = 'x_total_%s' % group['balance_group'])

	def insert_data(self,DynamicRecord,groups):
		total_active, total_pasive = 0, 0
		for group in groups:
			currents = self.env['financial.situation'].search([('group_balance','=',group['balance_group'])])
			total = 0
			for c,current in enumerate(currents):
				DynamicRecord.write({'x_%s_%s' % (c, group['balance_group']): current.total})
				total += current.total
			DynamicRecord.write({'x_total_%s' % group['balance_group']: total})
			if group['balance_group'] in ['B1','B2']:
				total_active += total
			else:
				total_pasive += total
		return total_active, total_pasive

	def get_window_financial_situation(self):
		GROUPS = [{'balance_group': 'B1', 'xml_group': 'activo_corriente', 'total': 'TOTAL ACTIVO CORRIENTE'},
				  {'balance_group': 'B2', 'xml_group': 'activo_no_corriente', 'total': 'TOTAL ACTIVO NO CORRIENTE'},
				  {'balance_group': 'B3', 'xml_group': 'pasivo_corriente', 'total': 'TOTAL PASIVO CORRIENTE'},
				  {'balance_group': 'B4', 'xml_group': 'pasivo_no_corriente', 'total': 'TOTAL PASIVO NO CORRIENTE'},
				  {'balance_group': 'B5', 'xml_group': 'patrimonio', 'total': 'TOTAL PATRIMONIO'}]

		self.delete_childs(GROUPS)
		DynamicModel = self.env['ir.model'].search([('model','=','dynamic.financial.situation')],limit=1)
		self.env['ir.model.fields'].search([('model_id','=',DynamicModel.id),('state','=','manual')]).unlink()
		self.env['dynamic.financial.situation'].search([]).unlink()
		form_view = self.env['ir.model.data'].xmlid_to_object('account_balance_rep_it.view_dynamic_financial_situation_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))
		
		self.generate_fields(xml_form, GROUPS, DynamicModel)
		
		self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_resultado_periodo',
						'field_description': 'RESULTADO PERIODO',
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
		xml_group = xml_form.xpath("//group[@id='resultado_periodo']")[0]
		etree.SubElement(xml_group, "field", name = 'x_resultado_periodo')
		self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_total_activo',
						'field_description': 'TOTAL ACTIVO',
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
		xml_group = xml_form.xpath("//group[@id='total_activo']")[0]
		etree.SubElement(xml_group, "field", name = 'x_total_activo')
		self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_total_pasivo',
						'field_description': 'TOTAL PASIVO Y PATRIMONIO',
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
		xml_group = xml_form.xpath("//group[@id='total_pasivo']")[0]
		etree.SubElement(xml_group, "field", name = 'x_total_pasivo')

		DynamicRecord = self.env['dynamic.financial.situation'].create({'name':'Estado de Situacion Financiera al %s' % self.period_to.date_end})

		total_active, total_pasive = self.insert_data(DynamicRecord,GROUPS)

		DynamicRecord.write({'x_resultado_periodo': total_active - total_pasive,
							 'x_total_activo': total_active,
							 'x_total_pasivo': total_pasive + (total_active - total_pasive)})

		form_view.write({'arch': etree.tostring(xml_form)})

		return {
			'type': 'ir.actions.act_window',
			'res_id': DynamicRecord.id,
			'res_model': 'dynamic.financial.situation',
			'view_mode': 'form',
			'views': [(False, 'form')],
		}

	def get_pdf_financial_situation(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Situacion_Financiera.pdf',pagesize=landscape(letter))
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		decimal_rounding = '%0.2f'
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		top_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					 ('VALIGN', (0, 0), (-1, -1), 'TOP')]
		internal_width = [7.5*cm,2.5*cm]
		internal_height = [0.5*cm]
		external_width = [10*cm,10*cm]
		spacer = Spacer(10, 20)
		currents_B1 = self.env['financial.situation'].search([('group_balance','=','B1')])
		currents_B2 = self.env['financial.situation'].search([('group_balance','=','B2')])
		currents_B3 = self.env['financial.situation'].search([('group_balance','=','B3')])
		currents_B4 = self.env['financial.situation'].search([('group_balance','=','B4')])
		currents_B5 = self.env['financial.situation'].search([('group_balance','=','B5')])

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE SITUACION FINANCIERA AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)

		data = [
			 [Paragraph('<strong>ACTIVO</strong>',style_left),'',
			  Paragraph('<strong>PASIVO Y PATRIMONIO</strong>',style_left),'']
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>ACTIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B1 = 0
		for current in currents_B1:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B1 += current.total
		t1 = Table(data,internal_width,y*internal_height)
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B3 = 0
		for current in currents_B3:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B3 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B1),style_right),
			 Paragraph('<strong>TOTAL PASIVO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B3),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)
		
		data = [
				[Paragraph('<strong>ACTIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B2 = 0
		for current in currents_B2:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B2 += current.total
		t1 = Table(data,internal_width,y*internal_height)
		t1.setStyle(TableStyle(simple_style))
		data = [
				[Paragraph('<strong>PASIVO NO CORRIENTE</strong>',style_left),'']
			   ]
		y = 1
		total_B4 = 0
		for current in currents_B4:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B4 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([[t1,t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			[Paragraph('<strong>TOTAL ACTIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B2),style_right),
			 Paragraph('<strong>TOTAL PASIVO NO CORRIENTE</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B4),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		data = [
				[Paragraph('<strong>PATRIMONIO</strong>',style_left),'']
			   ]
		y = 1
		total_B5 = 0
		for current in currents_B5:
			data.append([Paragraph(current.name,style_left),Paragraph(str(decimal_rounding % current.total),style_right)])
			y += 1
			total_B5 += current.total
		t2 = Table(data,internal_width,y*internal_height)
		t2.setStyle(TableStyle(simple_style))
		t3 = Table([['',t2]],external_width)
		t3.setStyle(TableStyle(top_style))
		elements.append(t3)

		data = [
			['','',
			 Paragraph('<strong>TOTAL PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total_B5),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		elements.append(spacer)

		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		data = [
			['','',
			 Paragraph('<strong>RESULTADO DEL PERIODO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % period_result),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		data = [
			[Paragraph('<strong>TOTAL ACTIVO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B1 + total_B2)),style_right),
			 Paragraph('<strong>TOTAL PASIVO Y PATRIMONIO</strong>',style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % (total_B3 + total_B4 + total_B5 + period_result)),style_right)]
		]
		t = Table(data,2*internal_width)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Situacion_Financiera.pdf', 'rb')
		return self.env['popup.it'].get_file('Situacion_Financiera.pdf',base64.encodestring(b''.join(f.readlines())))

	def get_excel_financial_situation(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Situacion_Financiera.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)
		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)
		
		centered = workbook.add_format({'bold': True})
		centered.set_align('center')
		centered.set_align('vcenter')
		centered.set_border(style=0)
		centered.set_text_wrap()
		centered.set_font_size(11)
		centered.set_font_name('Times New Roman')

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Situacion Financiera")
		worksheet.set_tab_color('blue')

		worksheet.merge_range('B1:F1', self.company_id.name, centered)
		worksheet.merge_range('B2:F2', 'ESTADO DE SITUACION FINANCIERA AL %s' % self.period_to.date_end, centered)
		worksheet.merge_range('B3:F3', '(Expresado en Nuevos Soles)', centered)
		
		####ACTIVO CORRIENTE####
		worksheet.write(5,1,'ACTIVO',formats['especial2'])
		worksheet.write(6,1,'ACTIVO CORRIENTE',formats['especial2'])
		x=7
		currents = self.env['financial.situation'].search([('group_balance','=','B1')])
		total_B1 = 0
		for current in currents:
			worksheet.write(x,1,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,2,current.total if current.total else '0.00',formats['numberdos'])
			total_B1 += current.total
			x += 1
		limit_a = x
		
		####PASIVO CORRIENTE####
		worksheet.write(5,4,'PASIVO Y PATRIMONIO',formats['especial2'])		
		worksheet.write(6,4,'PASIVO CORRIENTE',formats['especial2'])
		x=7
		currents = self.env['financial.situation'].search([('group_balance','=','B3')])
		total_B3 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B3 += current.total
			x += 1
		limit_b = x
		limit = limit_a if limit_a > limit_b else limit_b

		worksheet.write(limit,1,'TOTAL ACTIVO CORRIENTE',formats['especial2'])
		worksheet.write(limit,2,total_B1,formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO CORRIENTE',formats['especial2'])
		worksheet.write(limit,5,total_B3,formats['numbertotal'])
		limit += 2

		####ACTIVO NO CORRIENTE####
		x = limit
		worksheet.write(x,1,'ACTIVO NO CORRIENTE',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B2')])
		total_B2 = 0
		for current in currents:
			worksheet.write(x,1,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,2,current.total if current.total else '0.00',formats['numberdos'])
			total_B2 += current.total
			x += 1
		limit_a = x

		####PASIVO NO CORRIENTE####
		x = limit
		worksheet.write(x,4,'PASIVO NO CORRIENTE',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B4')])
		total_B4 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B4 += current.total
			x += 1
		limit_b = x

		limit = limit_a if limit_a > limit_b else limit_b

		worksheet.write(limit,1,'TOTAL ACTIVO NO CORRIENTE',formats['especial2'])
		worksheet.write(limit,2,total_B2,formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO NO CORRIENTE',formats['especial2'])
		worksheet.write(limit,5,total_B4,formats['numbertotal'])
		limit += 2

		####PATRIMONIO####
		x = limit
		worksheet.write(x,4,'PATRIMONIO',formats['especial2'])
		x += 1
		currents = self.env['financial.situation'].search([('group_balance','=','B5')])
		total_B5 = 0
		for current in currents:
			worksheet.write(x,4,current.name if current.name else '',formats['especial1'])
			worksheet.write(x,5,current.total if current.total else '0.00',formats['numberdos'])
			total_B5 += current.total
			x += 1
		limit = x
		worksheet.write(limit,4,'TOTAL PATRIMONIO',formats['especial2'])
		worksheet.write(limit,5,total_B5,formats['numbertotal'])
		limit += 2

		####RESULTADO DEL PERIODO####
		worksheet.write(limit,4,'RESULTADO DEL PERIODO',formats['especial2'])
		period_result = (total_B1 + total_B2) - (total_B3 + total_B4 + total_B5)
		worksheet.write(limit,5,period_result,formats['numbertotal'])
		limit += 1

		worksheet.write(limit,1,'TOTAL ACTIVO',formats['especial2'])
		worksheet.write(limit,2,(total_B1 + total_B2),formats['numbertotal'])
		worksheet.write(limit,4,'TOTAL PASIVO',formats['especial2'])
		worksheet.write(limit,5,(total_B3 + total_B4 + total_B5) + period_result,formats['numbertotal'])

		widths = [10,60,16,8,60,16,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Situacion_Financiera.xlsx', 'rb')
		return self.env['popup.it'].get_file('Situacion_Financiera.xlsx',base64.encodestring(b''.join(f.readlines())))