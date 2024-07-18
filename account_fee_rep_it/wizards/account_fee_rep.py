# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountFeeRep(models.TransientModel):
	_name = 'account.fee.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	date_ini = fields.Date(string=u'Fecha Inicial',required=True)
	date_end = fields.Date(string=u'Fecha Final',required=True)
	currency = fields.Selection([('pen','PEN'),('usd','USD')],string=u'Moneda',default='pen', required=True)
	type_show =  fields.Selection([('pantalla','Pantalla'),('excel','Excel')],string=u'Mostrar en', required=True, default='pantalla')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
				self.date_ini = fiscal_year.date_from
				self.date_end = fiscal_year.date_to
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		self.domain_dates()
		self.env.cr.execute("""
			CREATE OR REPLACE view account_fee_book as ("""+self._get_sql(self.date_ini,self.date_end,self.company_id.id,self.currency)+""")""")
			
		if self.type_show == 'pantalla':
			return {
				'name': 'Libros de Honorarios',
				'type': 'ir.actions.act_window',
				'res_model': 'account.fee.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_plame(self,type,x_date_ini,x_date_end,x_company):

		self.env.cr.execute("""
			CREATE OR REPLACE view account_fee_book as ("""+self._get_sql(x_date_ini,x_date_end,x_company.id,'pen')+""")""")

		direccion = self.env['main.parameter'].search([('company_id','=',x_company.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		ruc = x_company.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		name_doc = "0601"+str(x_date_ini.year)+str('{:02d}'.format(x_date_end.month))+str(ruc)

		recibos = self.env['account.fee.book'].search([])
		ctxt = ""
		separator = "|"
		
		if type == 1:
			name_doc += ".ps4"
			for recibo in recibos:
				ctxt += str(recibo.tdp) + separator
				ctxt += str(recibo.docp) + separator
				ctxt += str(recibo.apellido_p) + separator
				ctxt += str(recibo.apellido_m) + separator
				ctxt += str(recibo.namep) + separator
				ctxt += str(recibo.is_not_home) + separator
				ctxt += str(recibo.c_d_imp) if recibo.c_d_imp else '0'
				ctxt += separator
				ctxt = ctxt + """\r\n"""
		else:
			name_doc += ".4ta"
			for recibo in recibos:
				ctxt += str(recibo.tdp) + separator
				ctxt += str(recibo.docp) + separator
				ctxt += "R" + separator
				ctxt += str(recibo.serie) if recibo.serie else ''
				ctxt += separator
				ctxt += str(recibo.numero) if recibo.numero else ''
				ctxt += separator
				ctxt += str(recibo.renta) if recibo.renta else '0'
				ctxt += separator
				ctxt += str(recibo.fecha_e.strftime('%d/%m/%Y')) + separator
				ctxt += str(recibo.fecha_p.strftime('%d/%m/%Y')) if recibo.fecha_p else ''
				ctxt += separator
				ctxt += '0' if recibo.retencion == 0 else '1'
				ctxt += separator
				ctxt += '' + separator + '' + separator
				ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''+ctxt.encode("utf-8")))	

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libros_de_Honorarios.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBROS DE HONORARIOS############
		worksheet = workbook.add_worksheet("LIBROS DE HONORARIOS")
		worksheet.set_tab_color('blue')
		
		HEADERS = ['PERIODO','LIBRO','VOUCHER','FECHA E','FECHA P','TD','SERIE','NUMERO','TDP','RUC','AP. PATERNO',
				   'AP. MATERNO','NOMBRES','DIVISA','TC','RENTA','RETENCION','NETO P','PERIODO P','NO DOMICILIADO']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.fee.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,2,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,3,line.fecha_e if line.fecha_e else '',formats['dateformat'])
			worksheet.write(x,4,line.fecha_p if line.fecha_p else '',formats['dateformat'])
			worksheet.write(x,5,line.td if line.td else '',formats['especial1'])
			worksheet.write(x,6,line.serie if line.serie else '',formats['especial1'])
			worksheet.write(x,7,line.numero if line.numero else '',formats['especial1'])
			worksheet.write(x,8,line.tdp if line.tdp else '',formats['especial1'])
			worksheet.write(x,9,line.docp if line.docp else '',formats['especial1'])
			worksheet.write(x,10,line.apellido_p if line.apellido_p else '',formats['especial1'])
			worksheet.write(x,11,line.apellido_m if line.apellido_m else '',formats['especial1'])
			worksheet.write(x,12,line.namep if line.namep else '',formats['especial1'])
			worksheet.write(x,13,line.divisa if line.divisa else '',formats['especial1'])
			worksheet.write(x,14,line.tipo_c if line.tipo_c else '0.0000',formats['numbercuatro'])
			worksheet.write(x,15,line.renta if line.renta else '0.00',formats['numberdos'])
			worksheet.write(x,16,line.retencion if line.retencion else '0.00',formats['numberdos'])
			worksheet.write(x,17,line.neto_p if line.neto_p else '0.00',formats['numberdos'])
			worksheet.write(x,18,line.periodo_p if line.periodo_p else '',formats['especial1'])
			worksheet.write(x,19,line.is_not_home if line.is_not_home else '',formats['especial1'])
			x += 1

		widths = [9,7,11,9,9,4,5,10,4,11,10,10,15,5,7,12,12,12,9,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libros_de_Honorarios.xlsx', 'rb')

		return self.env['popup.it'].get_file('Libros_de_Honorarios.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self,x_date_ini,x_date_end,x_company_id,x_mon):

		if x_mon == 'pen':
			sql = """select 
				tt.id,
				tt.periodo,
				tt.libro,
				tt.voucher,
				tt.fecha_e,
				tt.fecha_p,
				tt.td,
				tt.serie,
				tt.numero,
				tt.tdp,
				tt.docp,
				tt.apellido_p,
				tt.apellido_m,
				tt.namep,
				tt.divisa,
				tt.tipo_c,
				tt.renta,
				tt.retencion,
				tt.neto_p,
				tt.periodo_p,
				tt.is_not_home,
				tt.c_d_imp,
				tt.company_id
				from get_recxhon_1_1(%s) tt
				where (tt.fecha_doc between '%s' and '%s')
			""" % (str(x_company_id),
				x_date_ini.strftime('%Y/%m/%d'),
				x_date_end.strftime('%Y/%m/%d'))
		else:
			sql = """select 
				tt.id,
				tt.periodo,
				tt.libro,
				tt.voucher,
				tt.fecha_e,
				tt.fecha_p,
				tt.td,
				tt.serie,
				tt.numero,
				tt.tdp,
				tt.docp,
				tt.apellido_p,
				tt.apellido_m,
				tt.namep,
				tt.divisa,
				tt.tipo_c,
				tt.renta_me as renta,
				tt.retencion_me as retencion,
				tt.neto_p_me as neto_p,
				tt.periodo_p,
				tt.is_not_home,
				tt.c_d_imp,
				tt.company_id
				from get_recxhon_1_1(%s) tt
				where (tt.fecha_doc between '%s' and '%s')
			""" % (str(x_company_id),
				x_date_ini.strftime('%Y/%m/%d'),
				x_date_end.strftime('%Y/%m/%d'))

		return sql
		
	def domain_dates(self):
		if self.date_ini:
			if self.exercise.date_from.year != self.date_ini.year:
				raise UserError("La fecha inicial no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_end:
			if self.exercise.date_from.year != self.date_end.year:
				raise UserError("La fecha final no esta en el rango del Año Fiscal escogido (Ejercicio).")
		if self.date_ini and self.date_end:
			if self.date_end < self.date_ini:
				raise UserError("La fecha final no puede ser menor a la fecha inicial.")
