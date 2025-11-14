# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountLetrasSaldosRep(models.TransientModel):
	_name = 'account.letras.saldos.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Cuentas_por_cobrar.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("CUENTAS POR COBRAR")
		worksheet.set_tab_color('blue')

		HEADERS = ['VENDEDOR','NRO DOCUMENTO','CLIENTE','FECHA EMISION', 'FECHA VENCIMIENTO', 'TIPO COMP', 'NRO COMP', 'MONEDA', 'P. VENTA MN', 'P. VENTA ME', 'PAGOS MN', 'PAGOS ME', 'SALDO MN', 'SALDO ME', 'DOC ORIGEN']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(self._get_sql(self.company_id,self.exercise,self.env.uid))
		res = self.env.cr.dictfetchall()
		if not self.env.user.has_group('saldos_cuentas_por_cobrar_it.group_accounts_receivable_balances_it'):
			res = filter(lambda line: line['vendedor'] == self.env.user.name, res)
		for line in res:
			worksheet.write(x,0,line['vendedor'] if line['vendedor'] else '',formats['especial1'])
			worksheet.write(x,1,line['nro_documento'] if line['nro_documento'] else '',formats['especial1'])
			worksheet.write(x,2,line['cliente'] if line['cliente'] else '',formats['especial1'])
			worksheet.write(x,3,line['fecha_emi'] if line['fecha_emi'] else '',formats['dateformat'])
			worksheet.write(x,4,line['fecha_ven'] if line['fecha_ven'] else '',formats['dateformat'])
			worksheet.write(x,5,line['tipo_comp'] if line['tipo_comp'] else '',formats['especial1'])
			worksheet.write(x,6,line['nro_comp'] if line['nro_comp'] else '',formats['especial1'])
			worksheet.write(x,7,line['moneda'] if line['moneda'] else '',formats['especial1'])
			worksheet.write(x,8,line['pventa_mn'] if line['pventa_mn'] else '0.00',formats['numberdos'])
			worksheet.write(x,9,line['pventa_me'] if line['pventa_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,10,line['pagos_mn'] if line['pagos_mn'] else '0.00',formats['numberdos'])
			worksheet.write(x,11,line['pagos_me'] if line['pagos_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,12,line['saldo_mn'] if line['saldo_mn'] else '0.00',formats['numberdos'])
			worksheet.write(x,13,line['saldo_me'] if line['saldo_me'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['doc_origin_customer'] if line['doc_origin_customer'] else '',formats['especial1'])
			x += 1

		widths = [15,18,40,18,22,13,13,9,13,13,13,13,13,13,15]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Cuentas_por_cobrar.xlsx', 'rb')
		return self.env['popup.it'].get_file('Cuentas_por_cobrar.xlsx',base64.encodestring(b''.join(f.readlines())))

	def _get_sql(self,company_id,fiscal_year,usuario):
		grupo = self.env['res.groups'].search([('name','=','Ver Todas las Facturas PC')]).id
		self.env.cr.execute("""
			select *
			from res_groups_users_rel
			where gid = """+str(grupo)+""" and uid = """+str(usuario))
		res = self.env.cr.dictfetchall()
		sql_vend = "and c1.vendedor = %s" % (str(usuario))
		
		if len(res) > 0:
			sql_vend = ""

		sql = """select 
				rpu.name as vendedor,
				rp.vat as nro_documento,
				rp.name as cliente,
				c1.fecha_emi,
				c1.fecha_ven,
				td.name as tipo_comp,
				c1.nro_comp,
				c3.name as moneda,
				case when c3.name='PEN'  THEN c2.pventa_mn else 0 end as pventa_mn,
				case when c3.name<>'PEN'  THEN c2.pventa_me else 0 end as pventa_me,
				case when c3.name='PEN'  THEN c2.pagos_mn else 0 end as pagos_mn,
				case when c3.name<>'PEN'  THEN c2.pagos_me else 0 end as pagos_me,
				case when c3.name='PEN' THEN c2.pventa_mn-c2.pagos_mn else 0 end as saldo_mn,
				case when c3.name<>'PEN' THEN c2.pventa_me-c2.pagos_me else 0 end as saldo_me,
				c1.doc_origin_customer
				from get_cab_cpc(%s) c1
				left join (select * from get_saldos_fxc('%s',%s)) c2 on c2.ide=c1.ide
				left join res_users ru on ru.id = c1.vendedor
				left join res_currency c3 on c3.id=c1.currency_id
				left join res_partner rpu on rpu.id = ru.partner_id
				left join res_partner rp on rp.id = c1.partner_id
				left join einvoice_catalog_01 td on td.id = c1.type_document_id
				where (c3.name='PEN' AND c2.pventa_mn-c2.pagos_mn <> 0) OR (c3.name<>'PEN' AND c2.pventa_me-c2.pagos_me <> 0)
				%s
			""" % (str(company_id.id),
				str(fiscal_year.name),
				str(company_id.id),
				sql_vend)

		return sql