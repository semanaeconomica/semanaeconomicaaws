from odoo import api, fields, models, tools
import calendar
from datetime import *
from decimal import *
from dateutil.relativedelta import relativedelta
import base64
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT

class HrLoan(models.Model):
	_name = 'hr.loan'
	_description = 'Loan'

	name = fields.Char()
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, required=True)
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	date = fields.Date(string='Fecha de Prestamo')
	amount = fields.Float(string='Monto de Prestamo')
	loan_type_id = fields.Many2one('hr.loan.type', string='Tipo de Prestamo')
	fees_number = fields.Integer(string='Numero de Cuotas')
	line_ids = fields.One2many('hr.loan.line', 'loan_id')
	observations = fields.Text(string='Observaciones')

	@api.onchange('employee_id', 'loan_type_id')
	def _get_name(self):
		for record in self:
			if record.employee_id and record.loan_type_id:
				record.name = '%s %s' % (record.loan_type_id.name, record.employee_id.name)

	def get_fees(self):
		self.line_ids.unlink()
		ReportBase = self.env['report.base']
		date = self.date
		debt = self.amount
		for c, fee in enumerate(range(self.fees_number), 1):
			last_day = calendar.monthrange(date.year,date.month)[1]
			if c == 1 and date.day == last_day:
				date = date + relativedelta(months=1)
			if c != 1:
				date = date + relativedelta(months=1)
			last_day = calendar.monthrange(date.year,date.month)[1]
			date = date.replace(day=last_day)
			fee_amount = ReportBase.custom_round(self.amount/self.fees_number, 2)
			debt -= fee_amount
			self.env['hr.loan.line'].create({
					'loan_id':self.id,
					'fee':c,
					'amount':fee_amount,
					'date':date,
					'debt':debt
				})
		return self.env['popup.it'].get_message('Se calculo Correctamente')

	def refresh_fees(self):
		total = self.amount
		for line in self.line_ids.sorted(lambda l: l.fee):
			total -= line.amount
			line.debt = total
		self.fees_number = len(self.line_ids)

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'prestamos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########ASISTENCIAS############
		worksheet = workbook.add_worksheet("PRESTAMOS")
		worksheet.set_tab_color('blue')

		worksheet.merge_range(1,0,1,4,"PRESTAMO %s %s"%(self.employee_id.name,self.date),formats['especial3'])
		worksheet.write(3,0,"Empleado",formats['boldbord'])
		worksheet.merge_range(3,1,3,2,self.employee_id.name,formats['especial1'])
		worksheet.write(3,3,"Fecha de Prestamo",formats['boldbord'])
		worksheet.write(3,4,self.date,formats['reverse_dateformat'])
		worksheet.write(5,0,"Tipo de Prestamo",formats['boldbord'])
		worksheet.merge_range(5,1,5,2,self.loan_type_id.name,formats['especial1'])
		worksheet.write(5,3,"Numero de Cuotas",formats['boldbord'])
		worksheet.write(5,4,self.fees_number,formats['especial1'])

		x = 7
		worksheet.write(x,0,"CUOTA",formats['boldbord'])
		worksheet.write(x,1,"MONTO",formats['boldbord'])
		worksheet.write(x,2,"FECHA DE PAGO",formats['boldbord'])
		worksheet.write(x,3,"DEUDA POR PAGAR",formats['boldbord'])
		worksheet.write(x,4,"VALIDACION",formats['boldbord'])
		x=8

		for line in self.line_ids:
			worksheet.write(x,0,line.fee if line.fee else 0,formats['numberdos'])
			worksheet.write(x,1,line.amount if line.amount else 0,formats['numberdos'])
			worksheet.write(x,2,line.date if line.date else '',formats['reverse_dateformat'])
			worksheet.write(x,3,line.debt if line.debt else 0,formats['numberdos'])
			worksheet.write(x,4,dict(line._fields['validation'].selection).get(line.validation) if line.validation else '',formats['especial1'])
			x += 1

		widths = [12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'prestamos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Prestamo - %s.xlsx' % self.date, base64.encodestring(b''.join(f.readlines())))

	def get_pdf(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		doc = SimpleDocTemplate(route + 'prestamos.pdf',pagesize=letter)
		elements = []
		style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, fontName="times-roman")
		style_cell = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=9.6, fontName="times-roman")
		simple_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]
		spacer = Spacer(10, 20)

		I = ReportBase.create_image(self.env.company.logo, MainParameter.dir_create_file + 'logo.jpg', 180.0, 35.0)
		data = [[I if I else '']]
		t = Table(data, [20 * cm])
		t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
							   ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
		elements.append(t)
		elements.append(spacer)

		elements.append(Paragraph("PRESTAMO %s - %s" % (self.employee_id.name, str(self.date)), style_title))
		elements.append(spacer)

		data = [[Paragraph('EMPLEADO', style_cell), Paragraph(self.employee_id.name, style_cell)],
				[Paragraph('FECHA PRESTAMO', style_cell), Paragraph(str(self.date), style_cell),
				 Paragraph('NUMERO CUOTAS', style_cell), Paragraph(str(self.fees_number), style_cell)]
				]
		t = Table(data,4*[1.4*inch],2*[0.4*inch])
		t.setStyle(TableStyle([
						('SPAN',(1,0),(3,0)),
						('ALIGN', (0, 0), (-1, -1), 'CENTER'),
						('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
			]))
		elements.append(t)

		elements.append(spacer)

		data = [[Paragraph('CUOTA', style_cell),
				Paragraph('MONTO', style_cell),
				Paragraph('FECHA DE PAGO', style_cell),
				Paragraph('DEUDA POR PAGAR', style_cell),
				Paragraph('VALIDACION', style_cell)],
				]
		y = 1
		for line in self.line_ids:
			data.append([
						Paragraph(str(line.fee) if line.fee else '', style_cell),
						Paragraph(str(line.amount) if line.amount else '0', style_cell),
						Paragraph(str(line.date) if line.date else '', style_cell),
						Paragraph(str(line.debt) if line.debt else '0', style_cell),
						Paragraph(dict(line._fields['validation'].selection).get(line.validation) if line.validation else '', style_cell)
					])
			y += 1
		t = Table(data, [0.8*inch, 1.0*inch, 1.4*inch, 1.4*inch, 1.4*inch], y*[0.3*inch])
		t.setStyle(TableStyle([
							('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4C5CF9")),
							('ALIGN', (0, 0), (-1, -1), 'CENTER'),
							('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
							('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
							('BOX', (0, 0), (-1, -1), 0.25, colors.black),
							]))
		elements.append(t)
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

		doc.build(elements)
		f = open(route + 'prestamos.pdf', 'rb')
		return self.env['popup.it'].get_file('Prestamo %s - %s.pdf' % (self.employee_id.name, self.date), base64.encodestring(b''.join(f.readlines())))

class HrLoanType(models.Model):
	_name = 'hr.loan.type'
	_description = 'Loan Type'

	name = fields.Char(string='Nombre')
	input_id = fields.Many2one('hr.payslip.input.type', string='Input')

class HrLoanLine(models.Model):
	_name = 'hr.loan.line'
	_description = 'Loan Line'

	loan_id = fields.Many2one('hr.loan', ondelete='cascade')
	employee_id = fields.Many2one(related='loan_id.employee_id', store=True)
	input_id = fields.Many2one(related='loan_id.loan_type_id.input_id', store=True)
	fee = fields.Integer(string='Cuota')
	amount = fields.Float(string='Monto')
	date = fields.Date(string='Fecha de Pago')
	debt = fields.Float(string='Deuda por Pagar')
	validation = fields.Selection([('not payed', 'NO PAGADO'), ('paid out', 'PAGADO')], string='Validacion', default='not payed')

	def turn_paid_out(self):
		for record in self:
			record.validation = 'paid out'

	def set_not_payed(self):
		for record in self:
			record.validation = 'not payed'