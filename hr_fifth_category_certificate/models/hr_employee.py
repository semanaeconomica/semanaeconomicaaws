# -*- coding:utf-8 -*-
from odoo import api, fields, models

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from datetime import *
import base64

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	def get_fifth_wizard(self):
		wizard = self.env['hr.fifth.category.wizard'].create({'name': 'Certificado Quinta'})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.fifth.category.wizard',
			'views': [[False, 'form']],
			'target': 'new',
			'context': {'employee_ids': self.ids}
		}

	def get_pdf_fifth_certificate(self, date, employee):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		FiscalYear = Liquidation.fiscal_year_id
		year = int(FiscalYear.name)
		Company = self.env.company
		Lot = Liquidation.payslip_run_id
		Fifth = self.env['hr.fifth.category'].search([('payslip_run_id', '=', Lot.id)])
		Fifth_Employee = Fifth.line_ids.filtered(lambda line: line.employee_id == self)
		Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == self)
		REQ_ROQ = sum(Slip.line_ids.filtered(lambda line: line.salary_rule_id in (MainParameter.fifth_afect_sr_id, MainParameter.fifth_extr_sr_id)).mapped('total'))
		Net_Rent = Fifth_Employee.real_other_emp_rem + REQ_ROQ
		Seven_Uit = 7 * FiscalYear.uit
		Total_Rent = Net_Rent - Seven_Uit
		Tax_Rent = self.env['hr.fifth.category.line'].get_tax_proy(Total_Rent, MainParameter.rate_limit_ids)
		Tax_Rent = 0 if Tax_Rent < 0 else Tax_Rent
		Lots = self.env['hr.payslip.run'].search([('date_start', '>=', FiscalYear.date_from),('date_end', '<=', Lot.date_end)])
		Slips = Lots.slip_ids.filtered(lambda slip: slip.employee_id == self)
		PastFifths = sum(Slips.input_line_ids.filtered(lambda line: line.input_type_id == MainParameter.fifth_category_input_id).mapped('amount'))
		elements = []
		style_title = ParagraphStyle(name='Title', alignment=TA_CENTER, fontSize=14, fontName="times-roman")
		style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=10, fontName="times-roman")
		style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10, fontName="times-roman")
		style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=10, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Left Tab', alignment=TA_LEFT, fontSize=10, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong>CERTIFICADO DE RENTAS Y RETENCIONES POR RENTAS DE QUINTA CATEGORÍA</strong>', style_center)],
				[Paragraph('<strong>(Art. 45 D.S. Nº 122.94-EF del 21/09/1994) (R.S. Nº 010-2006/SUNAT del 13/01/2006)</strong>', style_center)],
		]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>EJERCICIO GRAVABLE %s</strong>' % year, style_center)],
				[''],
				[Paragraph('{0} RUC Nro. {1} con domicilio fiscal en \
							{2} debidamente representada por el Sr./Sra./Srta. {3} en calidad\
							de Gerente General, identificado con DNI Nro. {4}'.format(Company.name or '',
																					  Company.vat or '',
																					  Company.street or '',
																					  employee.name or '',
																					  employee.identification_id or ''), style_left)],
				[''],
				[Paragraph('<strong>CERTIFICA:</strong>', style_left)],
				[''],
				[Paragraph(u'Que el Sr./Sra./Srta. {0} con Documento de identidad Nro. {1} \
							con domicilio en {2}, se le ha retenido por Impuesto a la Renta de Quinta \
							Categoría por sus funciones en el cargo de {3} correspondiente al ejercicio {4} \
							el importe de:'.format(self.name or '',
												   self.identification_id or '',
												   self.work_location or '',
												   self.job_title or '',
												   FiscalYear.name or ''), style_left)],
			]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)
		elements.append(spacer)
		data = [
				[Paragraph('<strong>1. Renta Bruta:</strong>', style_left)],
				[Paragraph('1.1. Sueldo, asignaciones, gratificaciones, bonificaciones, comisiones, etc.', style_left_tab), Paragraph('S/ %d' % REQ_ROQ, style_left)],
				[Paragraph('1.2. Ingresos percibidos en otros empleadores', style_left_tab), Paragraph('S/ %d' % Fifth_Employee.real_other_emp_rem, style_left)],
				[Paragraph(u'Remuneración Bruta Total', style_left_tab), Paragraph('S/ %d' % Net_Rent, style_left)],
				[''],
				[Paragraph(u'<strong>2. Deducción sobre renta de quinta categoría:</strong>', style_left)],
				[Paragraph('Menos: 7UIT', style_left_tab), Paragraph('S/ %d' % Seven_Uit, style_left)],
				[Paragraph('Total renta imponible ', style_left_tab), Paragraph('S/ %d' % Total_Rent, style_left)],
				[''],
				[Paragraph('<strong>3.	Impuesto a la renta:</strong>', style_left), Paragraph('S/ %d' % Tax_Rent, style_left)],
				[''],
				[Paragraph(u'<strong>4.	Total retención efectuada:</strong>', style_left), Paragraph('S/ %d' % PastFifths, style_left)],
				[''],
				[Paragraph('<strong>Saldo por regularizar:</strong>', style_left), Paragraph('S/ %d' % (Tax_Rent - PastFifths), style_left)],
				[''],
				[Paragraph('{0} {1} de {2} del {3}'.format(Company.city or '',
														   date.day,
														   MainParameter.get_month_name(date.month),
														   date.year), style_left)],
				[''],[''],[''],
				[Paragraph('<strong>__________________________<br/>Empleador</strong>', style_center),
				Paragraph('<strong>__________________________<br/>Trabajador</strong>', style_center)],
		]
		t = Table(data, [10 * cm, 10 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)
		elements.append(PageBreak())

		return elements