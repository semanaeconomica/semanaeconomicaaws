# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
from math import modf
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
import subprocess
import sys

def install(package):
	subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
	from PyPDF2 import PdfFileReader, PdfFileWriter
except:
	install('PyPDF2')

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'

	def send_vouchers_by_email(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		route = MainParameter.dir_create_file + 'Boleta.pdf'
		issues = []
		for payslip in self:
			Employee = payslip.employee_id
			doc = SimpleDocTemplate(route, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
			doc.build(payslip.generate_voucher())
			f = open(route, 'rb')
			input_pdf = PdfFileReader(f)
			output_pdf = PdfFileWriter()
			output_pdf.appendPagesFromReader(input_pdf)
			output_pdf.encrypt(Employee.identification_id)
			output_pdf_report = open(route, 'wb')
			output_pdf.write(output_pdf_report)
			output_pdf_report.close()
			output_pdf_report = open(route, 'rb')
			try:
				self.env['mail.mail'].create({
						'subject': 'Boleta del Periodo: %s - %s' % (payslip.date_from, payslip.date_to),
						'body_html':'Estimado (a) %s,<br/>'
									'Estamos adjuntando la Boleta de Pago del %s al %s,<br/>'
									'<strong>Nota: Para abrir su boleta es necesario colocar su dni como clave</strong>' % (Employee.name, payslip.date_from, payslip.date_to),
						'email_to': Employee.work_email,
						'attachment_ids': [(0, 0, {'name': 'Boleta de Pago %s.pdf' % Employee.name,
												   'datas': base64.encodestring(output_pdf_report.read())}
										)]
					}).send()
			except:
				issues.append(Employee.name)
		if issues:
			return self.env['popup.it'].get_message('No se pudieron enviar las Boletas de los siguientes Empleados: \n %s' % '\n'.join(issues))
		else:
			return self.env['popup.it'].get_message('Se enviaron todas las Boletas satisfactoriamente.')

	def get_vouchers(self, payslips=None):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Boleta.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
		elements = []
		if payslips:
			for payslip in payslips:
				elements += payslip.generate_voucher()
		else:
			elements += self.generate_voucher()
		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Boleta.pdf', 'rb')
		return self.env['popup.it'].get_file('Boleta.pdf',base64.encodestring(b''.join(f.readlines())))

	def generate_voucher(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_voucher_values()
		ReportBase = self.env['report.base']
		Employee = self.employee_id
		Contract = self.contract_id
		admission_date = self.env['hr.contract'].get_first_contract(Employee, Contract).date_start

		#### WORKED DAYS ####
		DNLAB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dnlab.mapped('code'))
		DSUB = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dsub.mapped('code'))
		EXT = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_ext.mapped('code'))
		DVAC = self.worked_days_line_ids.filtered(lambda wd: wd.code in MainParameter.wd_dvac.mapped('code'))
		DLAB = self.get_dlabs()
		DLAB_DEC_INT = modf(DLAB * Contract.resource_calendar_id.hours_per_day)
		EXT_DEC_INT = modf(sum(EXT.mapped('number_of_hours')))


		#### SALARY RULE CATEGORIES ####
		INCOME = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.income_categories.ids and sr.total > 0)
		DISCOUNTS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.discounts_categories.ids and sr.total > 0)
		CONTRIBUTIONS = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_categories.ids and sr.total > 0)
		CONTRIBUTIONS_EMP = self.line_ids.filtered(lambda sr: sr.category_id.id in MainParameter.contributions_emp_categories.ids)
		NET_TO_PAY = self.line_ids.filtered(lambda sr: sr.salary_rule_id == MainParameter.net_to_pay_sr_id)
		SRC = {'Ingresos': INCOME, 'Descuentos': DISCOUNTS, 'Aportes Trabajador': CONTRIBUTIONS}

		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=9.6, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=9.6, fontName="times-roman")
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(10, 20)

		I = ReportBase.create_image(self.company_id.logo, MainParameter.dir_create_file + 'logo.jpg', 180.0, 35.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('RUC: %s' % self.company_id.vat or '', style_cell),
				 Paragraph('Empleador: %s' % self.company_id.name or '', style_cell),
				 Paragraph('Periodo: %s - %s' % (self.date_from or '', self.date_to or ''), style_cell)],
			]
		t = Table(data, [6 * cm, 8 * cm, 6 * cm], [0.5 * cm])
		t.setStyle(TableStyle([
				('BACKGROUND', (0, 0), (-1, -1), bg_color),
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
							]))
		elements.append(t)
		elements.append(spacer)
		first_row = [
				[Paragraph('Documento de Identidad', style_cell), '',
				 Paragraph('Nombres y Apellidos', style_cell), '', '', '',
				 Paragraph(U'Situación', style_cell), ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph(u'Número', style_cell), '', '', '', '', '', ''],
				[Paragraph(Employee.type_document_id.name or '', style_cell),
				 Paragraph(Employee.identification_id or '', style_cell),
				 Paragraph(Employee.name or '', style_cell), '', '', '',
				 Paragraph(Contract.situation_id.name or '', style_cell), '']
			]
		first_row_format = [
				('SPAN', (0, 0), (1, 0)),
				('SPAN', (2, 0), (5, 1)),
				('SPAN', (6, 0), (7, 1)),
				('SPAN', (2, 2), (5, 2)),
				('SPAN', (6, 2), (7, 2)),
				('BACKGROUND', (0, 0), (-1, 1), bg_color)
			]
		second_row = [
				[Paragraph('Fecha de Ingreso', style_cell), '',
				 Paragraph('Tipo Trabajador', style_cell), '',
				 Paragraph('Regimen Pensionario', style_cell), '',
				 Paragraph('CUSPP', style_cell), ''],
				[Paragraph(str(admission_date) or '', style_cell), '',
				 Paragraph(Contract.worker_type_id.name or '', style_cell), '',
				 Paragraph(Contract.membership_id.name or '', style_cell), '',
				 Paragraph(Contract.cuspp or '', style_cell), '']
			]
		second_row_format =	[
				('SPAN', (0, 3), (1, 3)),
				('SPAN', (2, 3), (3, 3)),
				('SPAN', (4, 3), (5, 3)),
				('SPAN', (6, 3), (7, 3)),
				('SPAN', (0, 4), (1, 4)),
				('SPAN', (2, 4), (3, 4)),
				('SPAN', (4, 4), (5, 4)),
				('SPAN', (6, 4), (7, 4)),
				('BACKGROUND', (0, 3), (-1, 3), bg_color)
			]
		third_row = [
				[Paragraph(u'Días Laborados', style_cell),
				 Paragraph(u'Días no Laborados', style_cell),
				 Paragraph(u'Días Subsidiados', style_cell),
				 Paragraph(u'Condición', style_cell),
				 Paragraph('Jornada Ordinaria', style_cell), '',
				 Paragraph('Sobretiempo', style_cell), ''],
				['', '', '', '',
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell),
				 Paragraph('Total Horas', style_cell),
				 Paragraph('Minutos', style_cell)],
				[Paragraph(str(ReportBase.custom_round(DLAB)) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(sum(DNLAB.mapped('number_of_days')))) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(sum(DSUB.mapped('number_of_days')))) or '0', style_cell),
				 Paragraph(dict(Employee._fields['condition'].selection).get(Employee.condition) or '', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[1])) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(DLAB_DEC_INT[0] * 60)) or '0', style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[1])), style_cell),
				 Paragraph(str(ReportBase.custom_round(EXT_DEC_INT[0] * 60)) or '0', style_cell)]
			]
		third_row_format = [
				('SPAN', (0, 5), (0, 6)),
				('SPAN', (1, 5), (1, 6)),
				('SPAN', (2, 5), (2, 6)),
				('SPAN', (3, 5), (3, 6)),
				('SPAN', (4, 5), (5, 5)),
				('SPAN', (6, 5), (7, 5)),
				('BACKGROUND', (0, 5), (-1, 6), bg_color)
			]
		fourth_row = [
				[Paragraph(u'Otros empleadores por Rentas de 5ta categoría', style_cell), '', '', '',
				 Paragraph(Contract.other_employers or '', style_cell), '', '', '']
			]
		fourth_row_format = [
				('SPAN', (0, 8), (3, 8)),
				('SPAN', (4, 8), (7, 8)),
				('BACKGROUND', (0, 8), (3, 8), bg_color)
			]
		fifth_row = [
				[Paragraph(u'Motivo de Suspensión de Labores', style_cell), '', '', '', '', '', '', ''],
				[Paragraph('Tipo', style_cell),
				 Paragraph('Motivo', style_cell), '', '', '', '', '',
				 Paragraph('Nro Días', style_cell)]
			]
		fifth_row_format = [
				('SPAN', (0, 9), (-1, 9)),
				('SPAN', (1, 10), (6, 10)),
				('BACKGROUND', (0, 9), (-1, 10), bg_color)
			]
		span_limit = 11
		y = 0
		for line in Contract.work_suspension_ids:
			fifth_row += [
					[Paragraph(line.suspension_type_id.code or '', style_cell), 
					  Paragraph(line.reason or '', style_cell), '', '', '', '', '',
					  Paragraph(str(line.days) or '0', style_cell)]
				]
			fifth_row_format += [('SPAN', (1, span_limit), (6, span_limit))]
			span_limit += 1
			y += 1
		global_format = [
				('ALIGN', (0, 0), (-1, -1), 'CENTER'),
				('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
				('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
				('BOX', (0, 0), (-1, -1), 0.25, colors.black)
			]
		t = Table(first_row + second_row + third_row + fourth_row + fifth_row, 8 * internal_width, (y + 11) * [0.5 * cm])
		t.setStyle(TableStyle(first_row_format + second_row_format + third_row_format + fourth_row_format + fifth_row_format + global_format))
		elements.append(t)
		elements.append(spacer)

		data = [[
				Paragraph(u'Código', style_cell),
				Paragraph('Conceptos', style_cell),
				Paragraph('Ingresos S/.', style_cell),
				Paragraph('Descuentos S/.', style_cell),
				Paragraph('Neto S/.', style_cell)
			]]
		y = 0
		data_format = [('BACKGROUND', (0, 0), (-1, 0), bg_color)]
		for i in SRC:
			data += [[Paragraph(i, style_left), '', '', '', '']]
			y += 1
			data_format += [('SPAN', (0, y), (-1, y)),
							('BACKGROUND', (0, y), (-1, y), bg_color)]
			for line in SRC[i]:
				data += [[
						Paragraph(line.salary_rule_id.sunat_code or '', style_left),
						Paragraph(line.name or '', style_left),
						Paragraph(str(line.total) or '0.00' if line.category_id.type == 'in' else '', style_right),
						Paragraph(str(line.total) or '0.00' if line.category_id.type == 'out' else '', style_right), ''
					]]
				y += 1
		y += 1
		data += [[Paragraph(NET_TO_PAY.salary_rule_id.name or '', style_left), '', '', '', Paragraph(str(NET_TO_PAY.total) or '0.00', style_right)]]
		data_format += [
			('SPAN', (0, y), (3, y)),
			('BACKGROUND', (0, y), (-1, y), bg_color),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
			('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, 0), 0.25, colors.black),
			('BOX', (0, 0), (-1, -1), 0.25, colors.black)
		]
		t = Table(data, [3 * cm, 8 * cm, 3 * cm, 3 * cm, 3 * cm], (y + 1) * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)

		data = [[Paragraph('Aportes Empleador', style_left), '', '']]
		data_format = [('SPAN', (0, 0), (-1, 0)),
					   ('BACKGROUND', (0, 0), (-1, 0), bg_color),
					   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
					   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
					   ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
					   ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]
		y = 1
		for sr in CONTRIBUTIONS_EMP:
			data += [[Paragraph(sr.salary_rule_id.sunat_code or '', style_left),
					  Paragraph(sr.name or '', style_left),
					  Paragraph(str(sr.total) or '0.00', style_right)]]
			y += 1	

		t = Table(data, [3 * cm, 14 * cm, 3 * cm], y * [0.5 * cm])
		t.setStyle(TableStyle(data_format))
		elements.append(t)
		elements.append(spacer)
		elements.append(spacer)
		elements.append(spacer)

		I = ReportBase.create_image(MainParameter.signature, MainParameter.dir_create_file + 'signature.jpg', 160.0, 35.0)
		data = [
				['', I if I else ''],
				[Paragraph('<strong>__________________________</strong>', style_cell), 
				 Paragraph('<strong>__________________________</strong>', style_cell)],
				[Paragraph('<strong>FIRMA TRABAJADOR</strong>', style_cell), 
				 Paragraph('<strong>FIRMA EMPLEADOR</strong>', style_cell)]
			]
		t = Table(data, [10 * cm, 10 * cm], 3 * [0.5 * cm])
		t.setStyle(TableStyle(simple_style))
		elements.append(t)
		elements.append(PageBreak())
		return elements