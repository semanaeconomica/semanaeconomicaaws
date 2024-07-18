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

	liquidation_id = fields.Many2one('hr.liquidation')

	def get_liquidation_employee(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Liquidacion de Beneficios Sociales.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
		elements = []
		for record in self:
			if record.liquidation_id:
				elements += record.get_pdf_liquidation()
		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Liquidacion de Beneficios Sociales.pdf', 'rb')
		return self.env['popup.it'].get_file('Liquidacion de Beneficios Sociales.pdf',base64.encodestring(b''.join(f.readlines())))

	def get_pdf_liquidation(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		Liquidation = self.liquidation_id
		year = int(Liquidation.fiscal_year_id.name)
		cts_period = MainParameter.get_month_name(int(Liquidation.cts_type))
		gratification_period = MainParameter.get_month_name(int(Liquidation.gratification_type))
		Gratification_Line = Liquidation.gratification_line_ids.filtered(lambda line: line.employee_id == self)
		Cts_Line = Liquidation.cts_line_ids.filtered(lambda line: line.employee_id == self)
		Vacation_Line = Liquidation.vacation_line_ids.filtered(lambda line: line.employee_id == self)
		vacation_period_start = MainParameter.get_month_name(int(Vacation_Line.compute_date.month))
		vacation_period_end = MainParameter.get_month_name(int(Vacation_Line.cessation_date.month))
		total_income = Cts_Line.total_cts + Vacation_Line.total_vacation + Gratification_Line.total_grat + Gratification_Line.bonus_essalud
		total_discount = Vacation_Line.afp_jub + Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com + Vacation_Line.afp_si + Vacation_Line.onp
		total = ReportBase.custom_round(total_income - total_discount, 2)
		Lot = Liquidation.payslip_run_id
		Slip = Lot.slip_ids.filtered(lambda slip: slip.employee_id == self)
		Last_Contract = Slip.contract_id
		cessation_period = MainParameter.get_month_name(int(Last_Contract.date_end.month))
		First_Contract = self.env['hr.contract'].get_first_contract(self, Last_Contract)
		days, months = MainParameter.get_months_days_difference(First_Contract.date_start, Last_Contract.date_end)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=7.0, fontName="times-roman")
		style_right = ParagraphStyle(name='Center', alignment=TA_RIGHT, fontSize=7.0, fontName="times-roman")
		style_left = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=7.0, fontName="times-roman")
		style_left_tab = ParagraphStyle(name='Center', alignment=TA_LEFT, fontSize=7.0, fontName="times-roman", leftIndent=14)
		internal_width = [2.5 * cm]
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		bg_color = colors.HexColor("#c5d9f1")
		spacer = Spacer(5, 20)

		global_format = [
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 160.0, 32.0)
		data = [[I if I else '', Paragraph('LIQUIDACION BENEFICIOS SOCIALES <br/>\
											  LIQUIDACION BENEFICIOS SOCIALES QUE OTORGA <br/>\
											  %s' % self.env.company.name, style_cell)]]
		t = Table(data, [5 * cm, 15 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('ALIGN', (1, 0), (1, 0), 'CENTER'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		data = [
				[Paragraph('<strong>DATOS PERSONALES</strong>', style_left)],
				[Paragraph('<strong>Apellidos y Nombres</strong>', style_left_tab), ':', Paragraph(self.name or '', style_left)],
				[Paragraph(u'<strong>DNI N°</strong>', style_left_tab), ':', Paragraph(self.identification_id or '', style_left)],
				[Paragraph('<strong>Cargo</strong>', style_left_tab), ':', Paragraph(self.job_id.name or '', style_left)],
				[Paragraph('<strong>Fecha Ingreso</strong>', style_left_tab), ':', Paragraph(str(First_Contract.date_start) or '', style_left)],
				[Paragraph('<strong>Fecha Cese</strong>', style_left_tab), ':', Paragraph(str(Last_Contract.date_end) or '', style_left)],
				[Paragraph('<strong>Motivo</strong>', style_left_tab), ':', Paragraph(Last_Contract.situation_reason or '', style_left)],
				[Paragraph(u'<strong>Afiliación</strong>', style_left_tab), ':', Paragraph(Last_Contract.membership_id.name or '', style_left)],
				[Paragraph(u'<strong>Ultimo Sueldo Básico</strong>', style_left_tab), ':', Paragraph('%d NUEVOS SOLES' % Last_Contract.wage, style_left),
				 Paragraph('<strong>Tipo de Cambio</strong> %d' % Liquidation.exchange_type, style_left)],
				[Paragraph(u'<strong>Tiempo de Servicios</strong>', style_left_tab), ':', Paragraph('%d MES(ES) y %d DIA(S)' % (months, days), style_left)],
				[''],
				[Paragraph('<strong>BASES DE CALCULO</strong>', style_left)],
				[Paragraph('<strong>1. COMPENSACION POR TIEMPO DE SERVICIOS</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=cts_period, end=cessation_period, year=year), style_left)],
				[Paragraph('<strong>Monto a Pagar</strong>', style_left_tab), ':', Paragraph(str(Cts_Line.total_cts or 0.0), style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph(str(Cts_Line.months or 0.0), style_left)],
				[''],
				[Paragraph('<strong>2. VACACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {start_year} a {end} {end_year})</strong>'.format(start=vacation_period_start,
																									   start_year=Vacation_Line.admission_date.year,
																									   end=vacation_period_end,
																									   end_year=Vacation_Line.cessation_date.year), style_left)],
				[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph('%d' % Vacation_Line.total_vacation or 0.0, style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph('%d' % Vacation_Line.months or 0.0, style_left)],
				[''],
				[Paragraph('<strong>3. GRATIFICACIONES</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=gratification_period, end=cessation_period, year=year), style_left)],
				[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.total_grat or 0.0), style_left)],
				[Paragraph('<strong>BONIF EX.L. 30334</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.bonus_essalud or 0.0), style_left)],
				[Paragraph('<strong>Tiempo</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.months or 0.0), style_left)],
				[''],
				[Paragraph('<strong>4. LIQUIDACION</strong>', style_left)],
				[Paragraph('<strong>(Periodo {start} {year} a {end} {year})</strong>'.format(start=gratification_period, end=cessation_period, year=year), style_left)],
				[Paragraph('<strong>CTS Trunca</strong>', style_left_tab), ':', Paragraph(str(Cts_Line.total_cts or 0.0), style_left)],
				[Paragraph('<strong>Vacaciones Truncas</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.total_vacation or 0.0), style_left)],
				[Paragraph(u'<strong>Gratificación Trunca</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.total_grat or 0.0), style_left)],
				[Paragraph('<strong>BONIF EX.L. 30334</strong>', style_left_tab), ':', Paragraph(str(Gratification_Line.bonus_essalud or 0.0), style_left)],
				[''],
				[Paragraph('<strong>OTROS INGRESOS</strong>', style_left)],
				[''],
				[Paragraph('<strong>Total Ingresos</strong>', style_left_tab), '', Paragraph(str(ReportBase.custom_round(total_income, 2) or 0.0), style_right)],
				[''],
				[Paragraph('<strong>Aportes Trabajador</strong>', style_left_tab)],
				[Paragraph('<strong>AFP. PENSIONES</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_jub or 0.0), style_left)],
				[Paragraph('<strong>AFP. COM. PORC.</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_mixed_com + Vacation_Line.afp_fixed_com), style_left)],
				[Paragraph('<strong>AFP. SEGUROS</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.afp_si or 0.0), style_left)],
				[Paragraph('<strong>IMPORTE ONP</strong>', style_left_tab), ':', Paragraph(str(Vacation_Line.onp or 0.0), style_left)],
				[''],
				[Paragraph('<strong>OTROS DESCUENTOS</strong>', style_left)],
				[''],
				[Paragraph('<strong>Total Descuentos</strong>', style_left_tab), '', Paragraph(str(ReportBase.custom_round(total_discount, 2) or 0.0), style_right)],
				[Paragraph('<strong>Total a Pagar</strong>', style_left_tab), '', Paragraph(str(total or 0.0), style_right)],
		]
		t = Table(data, [8 * cm, 1 * cm , 5 * cm, 6 * cm], len(data) * [0.32 * cm])
		t.setStyle(TableStyle(global_format))
		elements.append(t)

		data = [
				[Paragraph('<strong>Neto a Pagar al Trabajador</strong>', style_left)],
				[Paragraph('<strong>SON {0} soles</strong>'.format(MainParameter.number_to_letter(total_income - total_discount)), style_left_tab)],
				['', '', '', Paragraph('{0} {1} de {2} del {3}'.format(self.env.company.city or '',
																	   date.today().day,
																	   MainParameter.get_month_name(date.today().month),
																	   date.today().year), style_cell)],
				[Paragraph('<strong>__________________________<br/>Dpto. de personal<br/>%s</strong>' % self.env.company.name or '', style_cell)],
				[Paragraph('<strong>CONSTANCIA DE RECEPCION</strong>', style_left)],
				[Paragraph('Declaro estar conforme con la presente liquidación, haber recibido el importe de la misma \
							así como el importe correspondiente a todas y cada una de mis remuneraciones y beneficios no \
							teniendo que reclamar en el futuro, quedando asi concluida la relación laboral.', style_cell)],
				[''],
				[Paragraph('<strong>__________________________<br/>%s<br/>%s</strong>' % (self.name or '', self.identification_id or ''), style_cell)],
		]
		t = Table(data, [8 * cm, 1 * cm , 5 * cm, 6 * cm])
		t.setStyle(TableStyle([
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('SPAN', (0, 5), (-1, 5)),
			('SPAN', (0, 7), (-1, 7)),
			('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
		]))
		elements.append(t)
		elements.append(PageBreak())

		return elements