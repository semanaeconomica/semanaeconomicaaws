# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from odoo.exceptions import UserError
from datetime import *
import base64

class HrFifthCategoryWizard(models.TransientModel):
	_name = 'hr.fifth.category.wizard'
	_description = 'Fifth Category Wizard'

	name = fields.Char()
	date = fields.Date(string='Fecha de Emision')
	employee_id = fields.Many2one('hr.employee', string='Representante')

	def get_fifth_certificate_employee(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		if not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc = SimpleDocTemplate(MainParameter.dir_create_file + 'Certificado Quinta Categoria.pdf', pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=20)
		elements = []
		Employees = self.env['hr.employee'].browse(self._context.get('employee_ids'))
		for record in Employees:
			if record.liquidation_id:
				elements += record.get_pdf_fifth_certificate(self.date, self.employee_id)
		doc.build(elements)
		f = open(MainParameter.dir_create_file + 'Certificado Quinta Categoria.pdf', 'rb')
		return self.env['popup.it'].get_file('Certificado Quinta Categoria.pdf',base64.encodestring(b''.join(f.readlines())))