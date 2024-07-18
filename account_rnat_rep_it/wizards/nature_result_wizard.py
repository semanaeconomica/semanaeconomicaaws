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
			{'name': 'MARGEN COMERCIAL' ,'code': 'N1'},
			{'name': 'MARGEN COMERCIAL' ,'code': 'N2'},
			{'name': 'TOTAL PRODUCCION' ,'code': 'N3'},
			{'name': 'VALOR AGREGADO' , 'code': 'N4'},
			{'name': 'EXCEDENTE (O INSUFICIENCIA) BRUTO EXPL.', 'code': 'N5'},
			{'name': 'RESULTADO ANTES DE PARTIC. E IMPUESTOS', 'code': 'N6'},
			{'name': 'RESULTADO DEL EJERCICIO', 'code': 'N7'}
		]

class NatureResultWizard(models.TransientModel):
	_name = 'nature.result.wizard'

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

	def _get_nature_result_sql(self):
		sql = """
		CREATE OR REPLACE VIEW nature_result AS 
		(
			SELECT row_number() OVER () AS id,
			at.name,
			at.group_nature,
			sum(debe) - sum(haber) as total,
			at.order_nature
			from get_bc_register('{period_from}','{period_to}',{company}) bcr
			left join account_account aa on aa.code = bcr.cuenta and aa.company_id = {company}
			left join account_type_it at on at.id = aa.account_type_it_id
			where group_nature is not null
			group by at.name,at.group_nature,at.order_nature
			order by at.order_nature
		)
		""".format(
				period_from = self.period_from.code,
				period_to = self.period_to.code,
				company = self.company_id.id
			)
		return sql

	def get_report(self):
		self._cr.execute(self._get_nature_result_sql())
		if self.type_show == 'pantalla':
			return self.get_window_nature_result()
		elif self.type_show == 'pdf':
			return self.get_pdf_nature_result()
		else:
			return self.get_excel_nature_result()

	def delete_childs(self):
		form_view = self.env['ir.model.data'].xmlid_to_object('account_rnat_rep_it.view_dynamic_nature_result_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))
		xml_group = xml_form.xpath("//group[@id='nature_result']")[0]
		for child in xml_group:
			child.getparent().remove(child)
		form_view.write({'arch': etree.tostring(xml_form)})

	def generate_fields(self,xml_form,groups,DynamicModel):
		for group in groups:
			currents = self.env['nature.result'].search([('group_nature','=',group['code'])])
			for c,current in enumerate(currents):
				self.env['ir.model.fields'].create({
						'model_id': DynamicModel.id,
						'name': 'x_%s_%s' % (c, group['code']),
						'field_description': current.name,
						'ttype': 'float',
						'state': 'manual',
						'readonly': 'true'
					})
				xml_group = xml_form.xpath("//group[@id='nature_result']")[0]
				etree.SubElement(xml_group, "field", name = 'x_%s_%s' % (c, group['code']))
			if group['code'] == 'N2':
				self.env['ir.model.fields'].create({
							'model_id': DynamicModel.id,
							'name': 'x_total_%s' % group['code'],
							'field_description': group['name'],
							'ttype': 'float',
							'state': 'manual',
							'readonly': 'true'
						})
				xml_group = xml_form.xpath("//group[@id='nature_result']")[0]
				etree.SubElement(xml_group, "field", name = 'x_total_%s' % group['code'])
			if group['code'] not in ['N1','N2']:
				self.env['ir.model.fields'].create({
							'model_id': DynamicModel.id,
							'name': 'x_total_%s' % group['code'],
							'field_description': group['name'],
							'ttype': 'float',
							'state': 'manual',
							'readonly': 'true'
						})
				xml_group = xml_form.xpath("//group[@id='nature_result']")[0]
				etree.SubElement(xml_group, "field", name = 'x_total_%s' % group['code'])

	def get_nature_totals(self,groups,totals):
		def get_sum_group(code):
			return next(filter(lambda t: t['code'] == code, totals))['sum']
		####Totals#####
		comercial_margin = get_sum_group('N1') + get_sum_group('N2')
		next(filter(lambda g: g['code'] == 'N2', groups))['total'] = comercial_margin
		next(filter(lambda g: g['code'] == 'N3', groups))['total'] = get_sum_group('N3')
		added_value = comercial_margin + get_sum_group('N3') + get_sum_group('N4')
		next(filter(lambda g: g['code'] == 'N4', groups))['total'] = added_value
		excedent = added_value + get_sum_group('N5')
		next(filter(lambda g: g['code'] == 'N5', groups))['total'] = excedent
		tax_result = excedent + get_sum_group('N6')
		next(filter(lambda g: g['code'] == 'N6', groups))['total'] = tax_result
		year_result = tax_result + get_sum_group('N7')
		next(filter(lambda g: g['code'] == 'N7', groups))['total'] = year_result
		return groups

	def insert_data(self,DynamicRecord,groups):
		for group in groups:
			currents = self.env['nature.result'].search([('group_nature','=',group['code'])])
			for c,current in enumerate(currents):
				DynamicRecord.write({'x_%s_%s' % (c, group['code']): -1.0 * current.total})
			if group['code'] == 'N2':
				DynamicRecord.write({'x_total_%s' % group['code']: group['total']})
			if group['code'] not in ['N1','N2']:
				DynamicRecord.write({'x_total_%s' % group['code']: group['total']})
					
	def get_window_nature_result(self):
		self.delete_childs()
		DynamicModel = self.env['ir.model'].search([('model','=','dynamic.nature.result')],limit=1)
		self.env['ir.model.fields'].search([('model_id','=',DynamicModel.id),('state','=','manual')]).unlink()
		self.env['dynamic.nature.result'].search([]).unlink()
		form_view = self.env['ir.model.data'].xmlid_to_object('account_rnat_rep_it.view_dynamic_nature_result_form')
		xml_form = etree.XML(bytes(bytearray(form_view.arch,'utf-8')))
		
		TOTALS = self.get_totals(ENV_GROUPS)

		GROUPS = self.get_nature_totals(ENV_GROUPS,TOTALS)

		self.generate_fields(xml_form, GROUPS, DynamicModel)

		DynamicRecord = self.env['dynamic.nature.result'].create({'name':'Estado de Resultados al %s' % self.period_to.date_end})

		self.insert_data(DynamicRecord,GROUPS)

		form_view.write({'arch': etree.tostring(xml_form)})

		return {
			'type': 'ir.actions.act_window',
			'res_id': DynamicRecord.id,
			'res_model': 'dynamic.nature.result',
			'view_mode': 'form',
			'views': [(False, 'form')],
		}

	def get_pdf_nature_result(self):
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		doc = SimpleDocTemplate(direccion + 'Resultado_por_Naturaleza.pdf',pagesize=letter)
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
		internal_width = [10*cm,2.5*cm]
		internal_height = [0.5*cm]
		spacer = Spacer(10, 20)

		elements.append(Paragraph('<strong>%s</strong>' % self.company_id.name, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>ESTADO DE RESULTADOS AL %s</strong>' % self.period_to.date_end, style_title))
		elements.append(Spacer(10, 10))
		elements.append(Paragraph('<strong>(Expresado en Nuevos Soles)</strong>', style_title))
		elements.append(spacer)

		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_nature_totals(ENV_GROUPS,TOTALS)

		data, y = [], 0
		for group in GROUPS:
			currents = self.env['nature.result'].search([('group_nature','=',group['code'])])
			limit, c = len(currents), 1
			for current in currents:
				data.append([Paragraph(current.name if current.name else '', style_left),
							 Paragraph(str(decimal_rounding % (-1.0 * current.total)) if current.total else '0.00', style_right)])
				y += 1
			if group['code'] == 'N2':
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0

			if group['code'] not in ['N1','N2']:
				data.append([Paragraph('<strong>%s</strong>' % group['name'], style_left),
							 Paragraph('<strong><u>%s</u></strong>' % str(decimal_rounding % group['total']), style_right)])
				y += 1
				t = Table(data, internal_width, y*internal_height)
				t.setStyle(TableStyle(simple_style))
				elements.append(t)
				elements.append(spacer)
				data, y = [], 0
				
		doc.build(elements)

		f = open(direccion +'Resultado_por_Naturaleza.pdf', 'rb')
		return self.env['popup.it'].get_file('Resultado_por_Naturaleza.pdf',base64.encodestring(b''.join(f.readlines())))

	def get_totals(self,groups):
		TOTALS = []
		for group in groups:
			currents = self.env['nature.result'].search([('group_nature','=',group['code'])]).mapped('total')
			total = {'sum': -1.0 * sum(currents), 'code': group['code']}
			TOTALS.append(total)
		return TOTALS

	def get_excel_nature_result(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Resultado_por_Naturaleza.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		####DELETING BORDERS####
		for i in ['especial2','especial1','numberdos','numbertotal']:
			formats[i].set_border(style = 0)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Resultado por Naturaleza")
		worksheet.set_tab_color('blue')

		worksheet.write(1,1,self.company_id.name,formats['especial2'])
		worksheet.write(2,1,'ESTADO DE RESULTADOS AL %s' % self.period_to.date_end,formats['especial2'])
		worksheet.write(3,1,'(Expresado en Nuevos Soles)',formats['especial2'])

		TOTALS = self.get_totals(ENV_GROUPS)
		GROUPS = self.get_nature_totals(ENV_GROUPS,TOTALS)
		
		x = 5
		for group in GROUPS:
			currents = self.env['nature.result'].search([('group_nature','=',group['code'])])
			for current in currents:
				worksheet.write(x, 1, current.name if current.name else '', formats['especial1'])
				worksheet.write(x, 2, -1.0 * current.total if current.total else '0.00', formats['numberdos'])
				x += 1
			if group['code'] == 'N2':
					worksheet.write(x, 1, group['name'], formats['especial2'])
					worksheet.write(x, 2, group['total'], formats['numbertotal'])
					x += 2
			if group['code'] not in ['N1','N2']:
				worksheet.write(x, 1, group['name'], formats['especial2'])
				worksheet.write(x, 2, group['total'], formats['numbertotal'])
				x += 2


		widths = [10,60,16]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Resultado_por_Naturaleza.xlsx', 'rb')
		return self.env['popup.it'].get_file('Resultado_por_Naturaleza.xlsx',base64.encodestring(b''.join(f.readlines())))