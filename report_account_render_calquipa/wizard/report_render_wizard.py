# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
import decimal

class ReportRenderWizard(models.TransientModel):
	_name = "report.render.wizard"
	
	type_show = fields.Selection([
			('xls', 'Excel'),
			('pdf', 'PDF')
		],string='Mostrar en',default='xls')
	statement_id = fields.Many2one('account.bank.statement',string='Rendicion', required=True)
		
	def get_report(self):
		import importlib
		import sys
		importlib.reload(sys)

		render = self.statement_id

		if self.type_show == 'xls':
			print('sdss')
			
			import io
			from xlsxwriter.workbook import Workbook

			ReportBase = self.env['report.base']
			direccion = self.env['main.parameter'].search([('company_id','=',render.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

			workbook = Workbook(direccion +'RendicionCalquipa.xlsx')
			workbook, formats = ReportBase.get_formats(workbook)

			worksheet = workbook.add_worksheet("EXTRACTOS BANCARIOS")
			worksheet.set_tab_color('blue')

			worksheet.merge_range(1,0,1,5, render.name, formats['especial2'])

			worksheet.write(3,0, "Fecha Entrega:", formats['especial2'])
			worksheet.write(4,0, "Empleado:", formats['especial2'])
			worksheet.write(5,0, "Monto Entregado:", formats['especial2'])
			worksheet.write(6,0, "Caja Entrega:", formats['especial2'])
			worksheet.write(7,0, "Medio Pago:", formats['especial2'])

			worksheet.write(3,3, "Nro Comprobante:", formats['especial2'])
			worksheet.write(4,3, "Memoria:", formats['especial2'])
			worksheet.write(5,3, u"Fecha Rendición:", formats['especial2'])
			worksheet.write(6,3, "Monto Rendido:", formats['especial2'])

			worksheet.write(3,1, render.date_surrender if render.date_surrender else '', formats['especialdate'])
			worksheet.write(4,1, render.employee_id.name if render.employee_id else '', formats['especial4'])
			worksheet.write(5,1, render.amount_surrender, formats['numberdosespecial'])
			worksheet.write(6,1, render.journal_id.name, formats['especial4'])
			worksheet.write(7,1, render.einvoice_catalog_payment_id.name if render.einvoice_catalog_payment_id else '', formats['especial4'])

			worksheet.write(3,4, render.comp_number if render.comp_number else '', formats['especial4'])
			worksheet.write(4,4, render.memory if render.memory else '', formats['especial4'])
			worksheet.write(5,4, render.date_render_it if render.date_render_it else '', formats['especialdate'])

			HEADERS = ['NUMERO','COMPROBANTE','FECHA','PERIODO','EMPRESA','IMPORTE']
			worksheet = ReportBase.get_headers(worksheet,HEADERS,9,0,formats['boldbord'])

			x=10
			tot = 0

			for line in render.line_ids:
				worksheet.write(x,0,line.move_name if line.move_name else '',formats['especial1'])
				worksheet.write(x,1,line.ref if line.ref else '',formats['especial1'])
				worksheet.write(x,2,line.date if line.date else '',formats['dateformat'])
				worksheet.write(x,3,render.accounting_date if render.accounting_date else '',formats['dateformat'])
				worksheet.write(x,4,line.partner_id.name if line.partner_id else '',formats['especial1'])
				worksheet.write(x,5,line.amount if line.amount else '0.00',formats['numberdos'])
				tot += line.amount if line.amount < 0 else 0
			
			worksheet.write(6,4, tot, formats['numberdosespecial'])
				
			widths = [18,35,8,18,60,15]
			worksheet = ReportBase.resize_cells(worksheet,widths)
			workbook.close()

			f = open(direccion +'RendicionCalquipa.xlsx', 'rb')

			return self.env['popup.it'].get_file('Entrega Rendir.xlsx',base64.encodestring(b''.join(f.readlines())))
		else:
			def particionar_text(c,tam):
				tet = ""
				for i in range(len(c)):
					tet += c[i]
					lines = simpleSplit(tet,'Helvetica',8,tam)
					if len(lines)>1:
						return tet[:-1]
				return tet

			def pdf_header(self,c,wReal,hReal,size_widths):
				c.setFont("Helvetica-Bold", 9)
				c.drawCentredString((wReal/2)+20,hReal-12, "%s"%(render.company_id.name))
				c.setFont("Helvetica-Bold", 9)
				c.setFillColor(colors.black)
				c.drawCentredString((wReal/2)+20,hReal-20, "*** ENTREGAS A RENDIR: %s ***"%(render.name))

				c.setFont("Helvetica-Bold", 7)
				c.drawString(30,hReal-60,'Fecha Entrega:')
				c.drawString(30,hReal-70,'Empleado:')
				c.drawString(30,hReal-80,'Monto Entregado:')
				c.drawString(30,hReal-90,'Caja Entrega:')
				c.drawString(30,hReal-100,'Medio Pago:')

				c.drawString(310,hReal-60,u'Número Comprobante:')
				c.drawString(310,hReal-70,'Memoria:')
				c.drawString(310,hReal-80,u'Fecha Rendición:')
				c.drawString(310,hReal-90,'Monto Rendido:')

				c.setFont("Helvetica", 7)
				c.drawString(100,hReal-60,particionar_text(render.date_surrender.strftime('%Y/%m/%d') if render.date_surrender else '',230))
				c.drawString(100,hReal-70,particionar_text(render.employee_id.name if render.employee_id else '',230))
				c.drawString(100,hReal-80,particionar_text(str(render.amount_surrender),230))
				c.drawString(100,hReal-90,particionar_text(render.journal_id.name,230))
				c.drawString(100,hReal-100,particionar_text(render.einvoice_catalog_payment_id.name if render.einvoice_catalog_payment_id else '',230))

				c.drawString(400,hReal-60,particionar_text(render.comp_number if render.comp_number else '',180))
				c.drawString(400,hReal-70,particionar_text(render.memory if render.memory else '',180))
				c.drawString(400,hReal-80,particionar_text(render.date_render_it.strftime('%Y/%m/%d') if render.date_render_it else '',180))
				tot = 0
				for l in render.line_ids:
					tot+= l.amount if l.amount < 0 else 0
				
				c.drawString(400,hReal-90,particionar_text(str(tot),200))

				c.setFont("Helvetica", 10)
				style = getSampleStyleSheet()["Normal"]
				style.leading = 8
				style.alignment= 1

				data= [[Paragraph(u"<font size=7><b>NÚMERO</b></font>",style), 
					Paragraph("<font size=7><b>COMPROBANTE</b></font>",style), 
					Paragraph("<font size=7><b>FECHA</b></font>",style), 
					Paragraph("<font size=7><b>PERIODO</b></font>",style), 
					Paragraph("<font size=7><b>EMPRESA</b></font>",style), 
					Paragraph("<font size=7><b>IMPORTE</b></font>",style)]]
				t=Table(data,colWidths=size_widths, rowHeights=(20))
				color_cab = colors.Color(red=(132/255),green=(133/255),blue=(133/255))
				t.setStyle(TableStyle([
					('GRID',(0,0),(-1,-1), 1, colors.black),
					('ALIGN',(0,0),(-1,-1),'LEFT'),
					('VALIGN',(0,0),(-1,-1),'MIDDLE'),
					('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
					('BACKGROUND', (0, 0), (5, 0),color_cab),
				]))
				t.wrapOn(c,30,500) 
				t.drawOn(c,30,hReal-130)

			def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
				if posactual <50:
					c.showPage()
					pdf_header(self,c,wReal,hReal,size_widths)
					return pagina+1,hReal-142
				else:
					return pagina,posactual-valor

			
			width ,height  = A4  # 595 , 842
			wReal = width- 15
			hReal = height - 40

			direccion = self.env['main.parameter'].search([('company_id','=',render.company_id.id)],limit=1).dir_create_file
			name_file = "RendicionCalquipa.pdf"
			c = canvas.Canvas( direccion + name_file, pagesize= A4 )
			pos_inicial = hReal-40
			pagina = 1

			size_widths = [80,93,45,50,187,70]

			pdf_header(self,c,wReal,hReal,size_widths)

			pos_inicial = pos_inicial-90

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
			tot = 0

			for i in render.line_ids:
				first_pos = 30
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+2 ,pos_inicial,particionar_text( i.move_name if i.move_name else '',80) )
				first_pos += size_widths[0]

				c.drawString( first_pos+2 ,pos_inicial,particionar_text( i.ref if i.ref else '',110) )
				first_pos += size_widths[1]

				c.drawString( first_pos+2 ,pos_inicial,particionar_text( i.date.strftime('%Y/%m/%d') if i.date else '',45) )
				first_pos += size_widths[2]

				c.drawString( first_pos+2 ,pos_inicial,particionar_text( render.accounting_date.strftime('%Y/%m/%d') if render.accounting_date else '',50) )
				first_pos += size_widths[3]

				c.drawString( first_pos+2 ,pos_inicial,particionar_text( i.partner_id.name if i.partner_id else '',215) )
				first_pos += size_widths[4]

				c.drawRightString( first_pos+65 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i.amount)) )
				tot += i.amount
				first_pos += size_widths[5]

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

			c.save()

			f = open(str(direccion) + name_file, 'rb')		
			return self.env['popup.it'].get_file('Entrega Rendir.pdf',base64.encodestring(b''.join(f.readlines())))
