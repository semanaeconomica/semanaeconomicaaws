# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from lxml import etree
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
ENV_GROUPS = [
			{'name': 'ACTIVIDADES DE OPERACION' ,'code': ['E1','E2'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE OPERACION'},
			{'name': 'ACTIVIDADES DE INVERSION' ,'code': ['E3','E4'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE INVERSION'},
			{'name': 'ACTIVIDADES DE FINANCIAMIENTO' ,'code': ['E5','E6'], 'total_name': 'AUMENTO (DISM) DEL EFECTIVO Y EQUIVALENTE DE EFECTIVO PROVENIENTES DE ACTIVIDADES DE FINANCIAMIENTO'}
		]

class EfectiveFlowWizard(models.TransientModel):
	_name = 'efective.flow.wizard'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string='Ejercicio',required=True)
	period_ini =  fields.Many2one('account.period',string='Periodo S. I.',required=True)
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

	def _get_efective_flow_sql(self):
		sql = """
		CREATE OR REPLACE VIEW efective_flow AS 
		(
			SELECT row_number() OVER () AS id,
			*
			from get_efective_flow('{period_from}','{period_to}','{period_ini}',{company})
		)
		""".format(
				period_from = self.period_from.date_start.strftime('%Y/%m/%d'),
				period_to = self.period_to.date_end.strftime('%Y/%m/%d'),
				period_ini = self.period_ini.code,
				company = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_efective_flow_sql())
		if self.type_show == 'pantalla':
			return self.get_window_efective_flow()
		elif self.type_show == 'pdf':
			return self.get_pdf_efective_flow()
		else:
			return self.get_excel_efective_flow()

	def delete_childs(self):
		form_view = self.env['ir.model.data'].xmlid_to_object('account_efective_rep_it.view_dynamic_efective_flow_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))
		for group in ENV_GROUPS:
			xml_group = xml_form.xpath("//group[@id='%s']" % group['code'][0])[0]
			for child in xml_group:
				child.getparent().remove(child)
			xml_group = xml_form.xpath("//group[@id='%s']" % group['code'][1])[0]
			for child in xml_group:
				child.getparent().remove(child)
		xml_group = xml_form.xpath("//group[@id='totales']")[0]
		for child in xml_group:
			child.getparent().remove(child)
		form_view.write({'arch': etree.tostring(xml_form)})

	def generate_fields(self,xml_form,groups,DynamicModel):
		def fast_create(DynamicId, name, description):
			self.env['ir.model.fields'].create({
					'model_id': DynamicId,
					'name': name,
					'field_description': description,
					'ttype': 'float',
					'state': 'manual',
					'readonly': 'true'
				})
		for group in groups:
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			for c,current in enumerate(currents_positive):
				fast_create(DynamicModel.id, 'x_%s_%s' % (c, group['code'][0]), current.name)
				xml_group = xml_form.xpath("//group[@id='%s']" % group['code'][0])[0]
				etree.SubElement(xml_group, "field", name = 'x_%s_%s' % (c, group['code'][0]))
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			for c,current in enumerate(currents_negative):
				fast_create(DynamicModel.id, 'x_%s_%s' % (c, group['code'][1]), current.name)
				xml_group = xml_form.xpath("//group[@id='%s']" % group['code'][1])[0]
				etree.SubElement(xml_group, "field", name = 'x_%s_%s' % (c, group['code'][1]))

			fast_create(DynamicModel.id, 'x_total_%s_%s' % (group['code'][0], group['code'][1]), group['total_name'])
			xml_group = xml_form.xpath("//group[@id='%s']" % group['code'][1])[0]
			etree.SubElement(xml_group, "field", name = 'x_total_%s_%s' % (group['code'][0], group['code'][1]))
		xml_group = xml_form.xpath("//group[@id='totales']")[0]
		fast_create(DynamicModel.id, 'x_efective_equivalent', 'AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO')
		etree.SubElement(xml_group, "field", name = 'x_efective_equivalent')
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for c,current in enumerate(currents):
			fast_create(DynamicModel.id, 'x_E7_E8_%s' % c, current.name)
			etree.SubElement(xml_group, "field", name = 'x_E7_E8_%s' % c)
		fast_create(DynamicModel.id, 'x_final_equivalent', 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO')
		etree.SubElement(xml_group, "field", name = 'x_final_equivalent')
			

	def insert_data(self,DynamicRecord,groups):
		for group in groups:
			total = 0
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			for c,current in enumerate(currents_positive):
				DynamicRecord.write({'x_%s_%s' % (c, group['code'][0]): current.total})
				total += current.total
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			for c,current in enumerate(currents_negative):
				DynamicRecord.write({'x_%s_%s' % (c, group['code'][1]): current.total})
				total += current.total
			DynamicRecord.write({'x_total_%s_%s' % (group['code'][0], group['code'][1]): total})
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		DynamicRecord.write({'x_efective_equivalent':sum(efective_equivalent)})
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for c,current in enumerate(currents):
			DynamicRecord.write({'x_E7_E8_%s' % (c): current.total})
		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		DynamicRecord.write({'x_final_equivalent': sum(final_equivalent)})

	def get_window_efective_flow(self):
		self.delete_childs()
		DynamicModel = self.env['ir.model'].search([('model','=','dynamic.efective.flow')],limit=1)
		self.env['ir.model.fields'].search([('model_id','=',DynamicModel.id),('state','=','manual')]).unlink()
		self.env['dynamic.efective.flow'].search([]).unlink()
		form_view = self.env['ir.model.data'].xmlid_to_object('account_efective_rep_it.view_dynamic_efective_flow_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))

		self.generate_fields(xml_form, ENV_GROUPS, DynamicModel)

		DynamicRecord = self.env['dynamic.efective.flow'].create({'name':'Estado de Flujos de Efectivo al %s' % self.period_to.date_end})

		self.insert_data(DynamicRecord,ENV_GROUPS)

		form_view.write({'arch': etree.tostring(xml_form)})

		return {
			'type': 'ir.actions.act_window',
			'res_id': DynamicRecord.id,
			'res_model': 'dynamic.efective.flow',
			'view_mode': 'form',
			'views': [(False, 'form')],
		}

	def get_pdf_efective_flow(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Flujo_Efectivo.pdf',pagesize=letter)
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
		internal_width = [12*cm,2.5*cm]
		internal_height = [1*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE FLUJOS DE EFECTIVO AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)
		
		for group in ENV_GROUPS:
			data, y, total = [], 0, 0
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left)])
			y += 1
			for current in currents_positive:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			data.append([Paragraph('<strong>Menos:</strong>', style_left),''])
			y += 1
			for current in currents_negative:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % current.total) if current.total else '0.00', style_right)])
				total += current.total
				y += 1
			data.append([Paragraph('<strong>%s</strong>' % group['total_name'], style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % total), style_right)])
			y += 1
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)
			elements.append(spacer)
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO</strong>', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(efective_equivalent)), style_right)]
		], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		
		data, y = [], 0
		for current in currents:
			data.append([Paragraph(current.name, style_left),
						 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % current.total), style_right)])
			y += 1
			
		if data:
			t = Table(data, internal_width, y*internal_height)
			t.setStyle(TableStyle(simple_style))
			elements.append(t)

		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		t = Table([
			[Paragraph('<strong>%s</strong>' % 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', style_left),
			 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % sum(final_equivalent)), style_right)]
			], internal_width, internal_height)
		t.setStyle(TableStyle(simple_style))
		elements.append(t)

		doc.build(elements)

		f = open(direccion +'Flujo_Efectivo.pdf', 'rb')
		return self.env['popup.it'].get_file('Flujo_Efectivo.pdf',base64.encodestring(b''.join(f.readlines())))

	def get_excel_efective_flow(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Flujo_Efectivo.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Flujo Efectivo")
		worksheet.set_tab_color('blue')

		worksheet.write(1,1,self.company_id.name,formats['especial2'])
		worksheet.write(2,1,'ESTADO DE FLUJOS DE EFECTIVO AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,1,'(Expresado en Nuevos Soles)',formats['especial2'])
		
		x = 5
		for group in ENV_GROUPS:
			currents_positive = self.env['efective.flow'].search([('efective_group','=',group['code'][0])])
			worksheet.write(x, 1, group['name'], formats['especial2'])
			total = 0
			x += 1
			for current in currents_positive:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			currents_negative = self.env['efective.flow'].search([('efective_group','=',group['code'][1])])
			worksheet.write(x, 1, 'Menos:', formats['especial2'])
			x += 1
			for current in currents_negative:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, current.total if current.total else '0.00', formats['numberdos'])
				total += current.total
				x += 1
			worksheet.write(x, 1, group['total_name'], formats['especial2'])
			worksheet.write(x, 2, total, formats['numbertotal'])
			x += 2
		efective_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6'])]).mapped('total')
		worksheet.write(x, 1, 'AUMENTOS (DISM) NETO DE EFECTIVO Y EQUIVALENTE DE EFECTIVO', formats['especial2'])
		worksheet.write(x, 2, sum(efective_equivalent), formats['numbertotal'])
		x += 1
		currents = self.env['efective.flow'].search([('efective_group','in',['E7','E8'])],order='efective_order')
		for current in currents:
			worksheet.write(x, 1, current.name if current.name else '',formats['especial2'])
			worksheet.write(x, 2, current.total if current.total else '0.00',formats['numbertotal'])
			x += 1
		final_equivalent = self.env['efective.flow'].search([('efective_group','in',['E1','E2','E3','E4','E5','E6','E7','E8'])]).mapped('total')
		worksheet.write(x, 1, 'SALDO AL FINALIZAR DE EFECTIVO Y EQUIVALENTE DE EFECTIVO AL FINALIZAR EL EJERCICIO', formats['especial2'])
		worksheet.write(x, 2, sum(final_equivalent), formats['numbertotal'])

		widths = [10,132,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Flujo_Efectivo.xlsx', 'rb')
		return self.env['popup.it'].get_file('Flujo_Efectivo.xlsx',base64.encodestring(b''.join(f.readlines())))