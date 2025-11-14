# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4,letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
import decimal

class AccountSunatRep(models.TransientModel):
	_name = 'account.sunat.rep'

	name = fields.Char()

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	exercise = fields.Many2one('account.fiscal.year',string=u'Ejercicio')
	period = fields.Many2one('account.period',string='Periodo')
	number = fields.Char(string='Numero')

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.exercise = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_txt_81(self):
		return self._get_ple(1)

	def get_txt_82(self):
		return self._get_ple(2)

	def get_txt_141(self):
		return self._get_ple(3)

	def get_txt_diario(self):
		return self._get_ple(4)

	def get_txt_plan_c(self):
		return self._get_ple(5)

	def get_txt_mayor(self):
		return self._get_ple(6)

	def get_txt_caja(self):
		return self._get_ple(8)

	def get_txt_banco(self):
		return self._get_ple(9)

	def get_txt_balance(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = self.number+str(ruc)+".txt"
		sql_ple,nomenclatura = self._get_sql(10)
		self.env.cr.execute(sql_ple)
		sql_ple = "COPY (%s) TO STDOUT WITH %s" % (sql_ple, "CSV DELIMITER '|'")
		rollback_name = self._create_savepoint()

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_ple, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			self._rollback_savepoint(rollback_name)

		res = res.decode('utf-8')

		return self.env['popup.it'].get_file(name_doc,res if res else base64.encodestring(b"== Sin Registros =="))

	def get_txt_servidores(self):
		FeeRep = self.env['account.fee.rep']
		return FeeRep.get_plame(1,self.period.date_start,self.period.date_end,self.company_id)
	
	def get_txt_recibos(self):
		FeeRep = self.env['account.fee.rep']		
		return FeeRep.get_plame(2,self.period.date_start,self.period.date_end,self.company_id)

	def get_pdt_pi(self):
		Perception = self.env['account.percep.rep']
		return Perception.get_txt(1,self.company_id,self.period.date_start,self.period.date_end)

	def get_pdt_p(self):
		Perception = self.env['account.percep.rep']
		return Perception.get_txt(0,self.company_id,self.period.date_start,self.period.date_end)

	def get_daot_purchase(self):
		return self.get_daot(self.get_sql_daot_purchase(),"Costos")

	def get_daot_sale(self):
		return self.get_daot(self.get_sql_daot_sale(),"Ingresos")

	def get_sql_daot_purchase(self):
		uit_value = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).uit_value
		sql = """
			SELECT 
			ROW_NUMBER() OVER() AS field1,
			litc.code_sunat AS field2,
			rpc.vat AS field3,
			'%s' AS field4,
			CASE
				WHEN rp.is_company = TRUE THEN '02'
				ELSE '01'
			END AS field5,
			lit.code_sunat AS field6,
			rp.vat AS field7,
			T1.montoc AS field8,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.last_name
			END AS field9,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.m_last_name
			END AS field10,
			CASE
				WHEN rp.is_company <> TRUE THEN split_part(rp.name_p, ' ', 1)
			END AS field11,
			CASE
				WHEN rp.is_company <> TRUE AND split_part(rp.name_p, ' ', 2) <> '' THEN split_part(rp.name_p, ' ', 2)
			END AS field12,
			CASE
				WHEN rp.is_company = TRUE THEN rp.name
			END AS field13,
			NULL AS field14
			FROM (select a1.partner_id,round(sum(a1.base1+a1.base2+a1.base3+a1.cng),0) as montoc, a1.company from vst_compras_1_1 a1
			left join res_partner a2 on a2.id=a1.partner_id
			where a2.is_not_home<>TRUE and a1.td<>'02' and a1.company = %s and left(a1.periodo,4) = '%s'
			group by a1.partner_id, a1.company
			having round(sum(a1.base1+a1.base2+a1.base3+a1.cng),0) >= %s)T1
			LEFT JOIN res_partner rp ON rp.id = T1.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			LEFT JOIN res_company rc ON rc.id = T1.company
			LEFT JOIN res_partner rpc ON rpc.id = rc.partner_id
			LEFT JOIN l10n_latam_identification_type litc ON litc.id = rpc.l10n_latam_identification_type_id
		""" % (self.exercise.name,
				str(self.company_id.id),
				self.exercise.name,
				str(uit_value*2))

		return sql

	def get_sql_daot_sale(self):
		param = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1)
		if not param.uit_value:
			raise UserError(u'No existe UIT configurado en Parametros Principales de Contabilidad para esta Compañía')
		if not param.sale_ticket_partner:
			raise UserError(u'No existe Partner para Boleta de Ventas configurado en Parametros Principales de Contabilidad para esta Compañía')

		sql = """
			SELECT 
			ROW_NUMBER() OVER() AS field1,
			litc.code_sunat AS field2,
			rpc.vat AS field3,
			'%s' AS field4,
			CASE
				WHEN rp.is_company = TRUE THEN '02'
				ELSE '01'
			END AS field5,
			lit.code_sunat AS field6,
			rp.vat AS field7,
			T1.montoc AS field8,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.last_name
			END AS field9,
			CASE
				WHEN rp.is_company <> TRUE THEN rp.m_last_name
			END AS field10,
			CASE
				WHEN rp.is_company <> TRUE THEN split_part(rp.name_p, ' ', 1)
			END AS field11,
			CASE
				WHEN rp.is_company <> TRUE AND split_part(rp.name_p, ' ', 2) <> '' THEN split_part(rp.name_p, ' ', 2)
			END AS field12,
			CASE
				WHEN rp.is_company = TRUE THEN rp.name
			END AS field13,
			NULL AS field14
			FROM (select am.partner_id,round(sum(a1.venta_g+a1.inaf+a1.exo),0) as montoc,a1.company from vst_ventas_1_1 a1
			LEFT JOIN account_move am ON am.id = a1.am_id
			LEFT JOIN res_partner a2 on a2.id=am.partner_id
			where a2.is_not_home<>TRUE and a1.td<>'02' and a1.company = %s and left(a1.periodo,4) = '%s' and am.partner_id <> %s
			group by am.partner_id,a1.company
			having round(sum(a1.venta_g+a1.inaf+a1.exo),0) >= %s)T1
			LEFT JOIN res_partner rp ON rp.id = T1.partner_id
			LEFT JOIN l10n_latam_identification_type lit ON lit.id = rp.l10n_latam_identification_type_id
			LEFT JOIN res_company rc ON rc.id = T1.company
			LEFT JOIN res_partner rpc ON rpc.id = rc.partner_id
			LEFT JOIN l10n_latam_identification_type litc ON litc.id = rpc.l10n_latam_identification_type_id
		""" % (self.exercise.name,
				str(self.company_id.id),
				self.exercise.name,
				str(param.sale_ticket_partner.id),
				str(param.uit_value*2))

		return sql

	def get_daot(self,sql,nomenclatura):

		name_doc = nomenclatura+".txt"
		self.env.cr.execute(sql)
		sql = "COPY (%s) TO STDOUT WITH %s" % (sql, "CSV DELIMITER '|'")
		rollback_name = self._create_savepoint()

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			self._rollback_savepoint(rollback_name)

		res = res.decode('utf-8')

		return self.env['popup.it'].get_file(name_doc,res if res else base64.encodestring(b"== Sin Registros =="))

	def get_pdb_currency_rate(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#RUC + .tc
		name_doc = str(ruc)+".tc"
		sql = self.get_sql_pdb_currency_rate()
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,4):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''+ctxt.encode("utf-8")))

	def get_sql_pdb_currency_rate(self):
		sql = """
				SELECT 
				TO_CHAR(rcr.name:: DATE, 'dd/mm/yyyy') AS field1,
				rcr.purchase_type AS field2,
				rcr.sale_type AS field3
				FROM res_currency_rate rcr
				LEFT JOIN res_currency rc ON rc.id = rcr.currency_id
				WHERE rc.name = 'USD' AND (rcr.name BETWEEN '%s' AND '%s')
				AND rcr.company_id = %s
				ORDER BY rcr.name
		""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

		return sql

	def get_pdb_purchase(self):
		ruc = self.company_id.partner_id.vat
		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#C + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "C"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+".txt"
		sql = self.get_sql_pdb_purchase()
		self.env.cr.execute(sql)

		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,31):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''+ctxt.encode("utf-8")))

	def get_sql_pdb_purchase(self):
		sql = """
				SELECT
				CASE
					WHEN rp.is_not_home = TRUE THEN '02'
					ELSE '01'
				END AS field1,
				vst_c.td AS field2,
				TO_CHAR(vst_c.fecha_e :: DATE, 'dd/mm/yyyy') AS field3,
				CASE
					WHEN vst_c.td in ('50','52','53','54') THEN vst_c.serie||vst_c.anio||vst_c.numero
					ELSE vst_c.serie
				END AS field4,
				CASE 
					WHEN vst_c.td in ('50','52','53','54') THEN ''
					ELSE vst_c.numero
				END AS field5,
				CASE
					WHEN rp.is_not_home = TRUE THEN '03'
					WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
					WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
				END AS field6,
				vst_c.tdp AS field7,
				vst_c.docp AS field8,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN rp.name
				END AS field9,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE rp.last_name
				END AS field10,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE rp.m_last_name
				END AS field11,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE split_part(rp.name_p, ' ', 1)
				END AS field12,
				CASE
					WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
					ELSE split_part(rp.name_p, ' ', 2)
				END AS field13,
				CASE
					WHEN vst_c.name = 'PEN' THEN '1'
					WHEN vst_c.name = 'USD' THEN '2'
					ELSE '3'
				END AS field14,
				pdb.cod_destino AS field15,
				pdb.nro_destino AS field16,
				abs(pdb.base) AS field17,
				abs(pdb.isc) AS field18,
				abs(pdb.igv) AS field19,
				abs(pdb.otros) AS field20,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN '1'
					ELSE '0'
				END AS field21,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN am.code_operation
				END AS field22,
				CASE
					WHEN am.linked_to_detractions = TRUE THEN am.voucher_number
				END AS field23,
				CASE
					WHEN am.campo_33_purchase = TRUE THEN '1'
					ELSE '0'
				END AS field24,
				ei.code AS field25,
				CASE
					WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
				END
				AS field26,
				CASE
					WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
					ELSE split_part(dr.nro_comprobante, '-', 1)
				END
				AS field27,
				TO_CHAR(dr.date :: DATE, 'dd/mm/yyyy') AS field28,
				CASE
					WHEN vst_c.name = 'PEN' THEN abs(dr.bas_amount)
					ELSE dr.bas_amount/am.currency_rate
				END AS field29,
				CASE
					WHEN vst_c.name = 'PEN' THEN abs(dr.tax_amount)
					ELSE dr.tax_amount/am.currency_rate
				END AS field30
				FROM vst_pdb_compras_2 pdb
				LEFT JOIN vst_compras_1_1 vst_c ON vst_c.am_id = pdb.move_id
				LEFT JOIN account_move am ON am.id = vst_c.am_id
				LEFT JOIN res_partner rp ON rp.id = am.partner_id
				LEFT JOIN ( SELECT a2.type_document_id,
									a2.date,
									a2.nro_comprobante,
									a2.amount_currency,
									a2.amount,
									a2.bas_amount,
									a2.tax_amount,
									a2.id,
									a2.move_id
								FROM doc_rela_pri a1
									LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = vst_c.am_id
				LEFT JOIN einvoice_catalog_01 ei ON ei.id = dr.type_document_id
				WHERE (vst_c.fecha_cont BETWEEN '%s' AND '%s') AND vst_c.company = %s
				AND vst_c.td not in ('00','02','09','19','20','31','40','96','99')
		""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

		return sql

	def get_pdb_sale(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#V + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "V"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+".txt"
		sql = self.get_sql_pdb_sale()
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,31):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''+ctxt.encode("utf-8")))

	def get_sql_pdb_sale(self):
		sql = """
			SELECT
			CASE
				WHEN rp.is_not_home = TRUE THEN '02'
				ELSE '01'
			END AS field1,
			vst_v.td AS field2,
			TO_CHAR(vst_v.fecha_e :: DATE, 'dd/mm/yyyy') AS field3,
			vst_v.serie AS field4,
			vst_v.numero AS field5,
			CASE
				WHEN rp.is_not_home = TRUE THEN '03'
				WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
				WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
			END AS field6,
			vst_v.tdp AS field7,
			vst_v.docp AS field8,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN rp.name
			END AS field9,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
			ELSE rp.last_name
			END AS field10,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE rp.m_last_name
			END AS field11,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE split_part(rp.name_p, ' ', 1)
			END AS field12,
			CASE
				WHEN (rp.is_not_home = TRUE) OR (rp.is_company = TRUE AND rp.is_not_home = FALSE) THEN NULL
				ELSE split_part(rp.name_p, ' ', 2)
			END AS field13,
			CASE
				WHEN vst_v.name = 'PEN' THEN '1'
				WHEN vst_v.name = 'USD' THEN '2'
				ELSE '3'
			END AS field14,
			pdb.cod_destino AS field15,
			pdb.nro_destino AS field16,
			abs(pdb.base) AS field17,
			abs(pdb.isc) AS field18,
			abs(pdb.igv) AS field19,
			abs(pdb.otros) AS field20,
			CASE
				WHEN am.linked_to_perception = TRUE THEN '1'
				ELSE '0'
			END AS field21,
			CASE
				WHEN am.linked_to_perception = TRUE THEN am.type_t_perception
			END AS field22,
			CASE
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) <> '' THEN split_part(am.number_perception, '-', 1)
			END AS field23,
			CASE
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) <> '' THEN split_part(am.number_perception, '-', 2)
				WHEN am.linked_to_perception = TRUE AND split_part(am.number_perception, '-', 2) = '' THEN split_part(am.number_perception, '-', 1)
			END AS field24,
			ei.code AS field25,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 1)
			END
			AS field26,
			CASE
				WHEN split_part(dr.nro_comprobante, '-', 2) <> '' THEN split_part(dr.nro_comprobante, '-', 2)
				ELSE split_part(dr.nro_comprobante, '-', 1)
			END
			AS field27,
			TO_CHAR(dr.date :: DATE, 'dd/mm/yyyy') AS field28,
			CASE
				WHEN vst_v.name = 'PEN' THEN abs(dr.bas_amount)
				ELSE round(dr.bas_amount/am.currency_rate,2)
			END AS field29,
			CASE
				WHEN vst_v.name = 'PEN' THEN abs(dr.tax_amount)
				ELSE round(dr.tax_amount/am.currency_rate,2)
			END AS field30
			FROM vst_pdb_ventas_2 pdb
			LEFT JOIN vst_ventas_1_1 vst_v ON vst_v.am_id = pdb.move_id
			LEFT JOIN account_move am ON am.id = vst_v.am_id
			LEFT JOIN res_partner rp ON rp.id = am.partner_id
			LEFT JOIN ( SELECT a2.type_document_id,
						a2.date,
						a2.nro_comprobante,
						a2.amount_currency,
						a2.amount,
						a2.bas_amount,
						a2.tax_amount,
						a2.id,
						a2.move_id
					FROM doc_rela_pri a1
					LEFT JOIN doc_invoice_relac a2 ON a1.min = a2.id) dr ON dr.move_id = vst_v.am_id
			LEFT JOIN einvoice_catalog_01 ei ON ei.id = dr.type_document_id
			WHERE (vst_v.fecha_cont BETWEEN '%s' AND '%s') AND vst_v.company = %s
		""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))
		return sql

	def get_pdb_payment(self):
		ruc = self.company_id.partner_id.vat

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		#F + RUC + AÑO(YYYY) + MES(MM) + .txt
		name_doc = "F"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+".txt"
		sql = self.get_sql_pdb_payment()
		self.env.cr.execute(sql)
		
		dicc = self.env.cr.dictfetchall()
		ctxt = ""
		separator = "|"
		
		for elem in dicc:
			for i in range(1,13):
				ctxt += str(elem['field%s'%(i)]) if elem['field%s'%(i)] else ''
				ctxt += separator
			ctxt = ctxt + """\r\n"""

		import importlib
		import sys
		importlib.reload(sys)

		return self.env['popup.it'].get_file(name_doc,base64.encodestring(b''+ctxt.encode("utf-8")))

	def get_sql_pdb_payment(self):
		sql = """
				SELECT 
				CASE
					WHEN rp.is_not_home = TRUE THEN '02'
					ELSE '01'
				END AS field1,
				vst_c.td AS field2,
				CASE
					WHEN vst_c.td in ('50','52','53','54') THEN vst_c.serie||vst_c.anio||vst_c.numero
					ELSE vst_c.serie
				END AS field3,
				CASE 
					WHEN vst_c.td in ('50','52','53','54') THEN ''
					ELSE vst_c.numero
				END AS field4,
				CASE
					WHEN rp.is_not_home = TRUE THEN '03'
					WHEN rp.is_company = FALSE AND rp.is_not_home <> TRUE THEN '01'
					WHEN rp.is_company = TRUE AND rp.is_not_home <> TRUE THEN '02'
				END AS field5,
				vst_c.tdp AS field6,
				vst_c.docp AS field7,
				pay.medio_pago AS field8,
				CASE 
					WHEN pay.medio_pago not in ('009','011','013','014','098') THEN pay.code_bank
				END AS field9,
				pay.field10,
				CASE 
					WHEN pay.medio_pago not in ('009','098') THEN TO_CHAR(pay.fecha :: DATE, 'dd/mm/yyyy')
				END AS field11,
				pay.monto AS field12
				FROM vst_compras_1_1 vst_c
				LEFT JOIN res_partner rp ON rp.id = vst_c.partner_id
				INNER JOIN (
				SELECT  
				a1.partner_id,
				a1.account_id,
				a1.td_sunat,
				a1.nro_comprobante,
				a1.cuenta,
				a1.medio_pago,
				a4.code_bank,
				a4.account_number,
				CASE
					WHEN a1.medio_pago in ('009','011','013','014') THEN NULL
					WHEN a4.code_bank = '99' THEN a4.financial_entity
					WHEN a4.code_bank <> '99' THEN a5.glosa
				END AS field10,
				a1.fecha,
				a1.moneda,
				CASE
					WHEN a1.moneda<>'PEN' THEN importe_me 
					ELSE debe 
				END AS monto
				FROM vst_diariog a1
				LEFT JOIN account_journal a2 ON a2.id=a1.journal_id
				LEFT JOIN account_account a3 ON a3.id=a1.account_id
				LEFT JOIN account_account a4 ON a4.id=a2.default_debit_account_id
				LEFT JOIN account_move a5 ON a5.id = a1.move_id
				WHERE a2.type IN ('bank','cash') AND a3.internal_type='payable' AND a1.debe IS NOT null
				) pay ON pay.partner_id||pay.td_sunat||pay.nro_comprobante = vst_c.partner_id || vst_c.td  || CASE WHEN vst_c.serie is null THEN vst_c.numero ELSE vst_c.serie||'-'||vst_c.numero END
				WHERE (vst_c.fecha_cont BETWEEN '%s' AND '%s') AND vst_c.company = %s
				AND vst_c.td not in ('00','02','09','19','20','31','40','96','99')
		""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

		return sql

	def _get_sql(self,type):
		PurchaseRep = self.env['account.purchase.rep']
		SaleRep = self.env['account.sale.rep']
		JournalRep = self.env['account.journal.rep']
		FeeRep = self.env['account.fee.rep']
		sql = ""
		nomenclatura = ""

		if type == 1:
			#SQL Compras 8.1
			sql = PurchaseRep._get_sql_ple81(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "080100"
		if type == 2:
			#SQL Compras 8.2
			sql = PurchaseRep._get_sql_ple82(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "080200"
		if type == 3:
			#SQL Ventas 14.1
			sql = SaleRep._get_sql_ple141(self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "140100"
		if type == 4:
			#SQL Libro Diario
			sql = JournalRep._get_sql_ple(1,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "050100"
		if type == 5:
			#SQL Plan Contable
			sql = JournalRep._get_sql_ple(3,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "050300"
		if type == 6:
			#SQL Libro Mayor
			sql = JournalRep._get_sql_ple(2,self.period.date_start,self.period.date_end,self.company_id.id)
			nomenclatura = "060100"
		if type == 7:
			#SQL Rec de Honorarios
			sql = FeeRep._get_sql(self.period.date_start,self.period.date_end,self.company_id.id,'pen')

		if type == 8:
			cash_account_prefix = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).cash_account_prefix
			sql = """
					SELECT 						
					CASE						
					WHEN right(a1.periodo,2) = '00' THEN left(a1.periodo,4) ||'0100'						
					WHEN right(a1.periodo,2) = '13' THEN left(a1.periodo,4) ||'1200'						
					ELSE a1.periodo || '00'						
					END AS campo1,						
					a2.cuo AS campo2,						
					CASE						
					WHEN right(a1.periodo,2) = '00' THEN 'A' || a1.voucher						
					WHEN right(a1.periodo,2) = '13' THEN 'C' || a1.voucher						
					ELSE 'M' || a1.voucher						
					END AS campo3,						
					a1.cuenta as campo4,						
					' '::text as campo5,						
					' '::text as campo6,						
					a1.moneda as campo7,						
					a1.td_sunat as campo8,						
					CASE						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE ' '						
					END AS campo9,						
					CASE
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) <> 0 THEN split_part(a1.nro_comprobante, '-', 2)						
					WHEN a1.nro_comprobante is not null and position('-' in a1.nro_comprobante::text) = 0 THEN split_part(a1.nro_comprobante, '-', 1)						
					ELSE '0'						
					END AS campo10,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo11,						
					' '::text as campo12,						
					TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo13,						
					a1.glosa as campo14,						
					' '::text as campo15,						
					a1.debe as campo16,						
					a1.haber as campo17,						
					' '::text as campo18,						
					a1.ple_diario as campo19,						
					' '::text as campo20						
					FROM vst_diariog a1						
					LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id						
					WHERE a1.periodo='%s'  and left(cuenta,3) in (%s)
					AND a1.company_id = %s
			""" % (self.period.code,cash_account_prefix,str(self.company_id.id))
			nomenclatura = "010100"

		if type == 9:
			bank_account_prefix = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).bank_account_prefix
			sql = """
				SELECT 
				CASE
				WHEN right(a1.periodo,2) = '00' THEN left(a1.periodo,4) ||'0100'
				WHEN right(a1.periodo,2) = '13' THEN left(a1.periodo,4) ||'1200'
				ELSE a1.periodo || '00'
				END AS campo1,
				a2.cuo AS campo2,
				CASE
				WHEN right(a1.periodo,2) = '00' THEN 'A' || a1.voucher
				WHEN right(a1.periodo,2) = '13' THEN 'C' || a1.voucher
				ELSE 'M' || a1.voucher
				END AS campo3,
				a3.code_bank as campo4,
				a3.account_number as campo5,
				TO_CHAR(a1.fecha::DATE, 'dd/mm/yyyy') as campo6,
				a1.medio_pago as campo7,
				a1.glosa as campo8,
				a1.td_partner as campo9,
				a1.doc_partner as campo10,
				a1.partner as campo11,
				a1.nro_comprobante as campo12,
				a1.debe as campo13,
				a1.haber as campo14,
				a1.ple_diario as campo15,
				' '::text as campo16
				fROM vst_diariog a1
				LEFT JOIN account_move_line a2 on a2.id=a1.move_line_id
				LEFT JOIN account_account a3 on a3.id=a1.account_id
				WHERE a1.periodo='%s'  and left(cuenta,3) in (%s)
				AND a1.company_id = %s
			""" % (self.period.code,bank_account_prefix,str(self.company_id.id))
			nomenclatura = "010200"

		if type == 10:
			sql = """
					SELECT 	
					distinct cta.code_sunat as c1,	
					coalesce(si.debe,0.00) as c2,	
					coalesce(si.haber,0.00) as c3,
					coalesce(mv.debe,0.00) as c4,
					coalesce(mv.haber,0.00) as c5,
					coalesce(0,0.00) as c6,	
					coalesce(0,0.00) as c7,	
					coalesce(0,0.00) as c8,
					coalesce(0,0.00) as c9,	
					null as c10	
					FROM vst_diariog bc	
					LEFT JOIN (SELECT code,code_sunat FROM account_account WHERE company_id=%s) cta on cta.code=bc.cuenta 	
					LEFT JOIN
					(	
					SELECT cta.code_sunat,sum(debe) as debe,sum(haber) as haber FROM vst_diariog a1	
					LEFT JOIN (SELECT code,code_sunat FROM account_account WHERE company_id=%s) cta on cta.code=a1.cuenta  	
					WHERE periodo='%s' and company_id=%s
					GROUP BY cta.code_sunat	
					) si on si.code_sunat=cta.code_sunat	
					LEFT JOIN
					(	
					SELECT code_sunat,sum(debe) as debe,sum(haber) as haber FROM vst_diariog b1 	
					LEFT JOIN (SELECT code,code_sunat FROM account_account WHERE company_id=%s) cta on cta.code=b1.cuenta	
					WHERE company_id=%s and (cast(periodo as numeric) between %s and %s)	
					GROUP BY cta.code_sunat	
					)mv on mv.code_sunat=cta.code_sunat	
						
					WHERE company_id=%s and 	
					left(bc.periodo,4)='%s' and 	
					left(cta.code_sunat,1)<>'9'	
					AND cta.code_sunat <> ''
					order by cta.code_sunat	
			""" % (str(self.company_id.id),
				str(self.company_id.id),
				str(self.exercise.name+'00'),
				str(self.company_id.id),
				str(self.company_id.id),
				str(self.company_id.id),
				str(self.exercise.name+'01'),
				str(self.exercise.name+'12'),
				str(self.company_id.id),
				str(self.exercise.name))

		return sql,nomenclatura

	def _get_ple(self,type):
		ruc = self.company_id.partner_id.vat
		mond = self.company_id.currency_id.name

		if not ruc:
			raise UserError('No configuro el RUC de su Compañia.')

		if not mond:
			raise UserError('No configuro la moneda de su Compañia.')

		#LE + RUC + AÑO(YYYY) + MES(MM) + DIA(00) 
		name_doc = "LE"+str(ruc)+str(self.period.date_start.year)+str('{:02d}'.format(self.period.date_start.month))+"00"
		sql_ple,nomenclatura = self._get_sql(type)
		self.env.cr.execute(sql_ple)
		sql_ple = "COPY (%s) TO STDOUT WITH %s" % (sql_ple, "CSV DELIMITER '|'")
		rollback_name = self._create_savepoint()

		try:
			output = BytesIO()
			self.env.cr.copy_expert(sql_ple, output)
			res = base64.b64encode(output.getvalue())
			output.close()
		finally:
			self._rollback_savepoint(rollback_name)

		res = res.decode('utf-8')

		# IDENTIFICADOR DEL LIBRO

		name_doc += nomenclatura

		# CODIGO DE OPORTUNIDAD DE PRESENTACION DEL EEFF (00) +
		# INDICADOR DE OPERACIONES (1) +
		# INDICADOR DE CONTENIDO Con informacion(1), Sin informacion(0) +
		# INDICADOR DE MONEDA UTILIZADA Nuevos Soles(1), US Dolares(2) +
		# INDICADOR DE LIBRO ELECTRONICO GENERADO POR EL PLE (1)

		name_doc += "00"+"1"+("1" if len(res) > 0 else "0") + ("1" if mond == 'PEN' else "2") + "1.txt"

		return self.env['popup.it'].get_file(name_doc,res if res else base64.encodestring(b"== Sin Registros =="))

	@api.model
	def _create_savepoint(self):
		rollback_name = '%s_%s' % (
			self._name.replace('.', '_'), uuid.uuid1().hex)
		req = "SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)
		return rollback_name

	@api.model
	def _rollback_savepoint(self, rollback_name):
		req = "ROLLBACK TO SAVEPOINT %s" % (rollback_name)
		self.env.cr.execute(req)

	def get_excel_81(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Compras_81.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(1)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36','CAMPO 37','CAMPO 38','CAMPO 39','CAMPO 40','CAMPO 41','CAMPO 42']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '0.00',formats['numberdos'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '0.00',formats['numberdos'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '',formats['especial1'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '',formats['especial1'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			worksheet.write(x,34,line['campo35'] if line['campo35'] else '',formats['especial1'])
			worksheet.write(x,35,line['campo36'] if line['campo36'] else '',formats['especial1'])
			worksheet.write(x,36,line['campo37'] if line['campo37'] else '',formats['especial1'])
			worksheet.write(x,37,line['campo38'] if line['campo38'] else '',formats['especial1'])
			worksheet.write(x,38,line['campo39'] if line['campo39'] else '',formats['especial1'])
			worksheet.write(x,39,line['campo40'] if line['campo40'] else '',formats['especial1'])
			worksheet.write(x,40,line['campo41'] if line['campo41'] else '',formats['especial1'])
			worksheet.write(x,41,line['campo42'] if line['campo42'] else '',formats['especial1'])
			x+=1

		
		widths = [10,22,12,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Compras_81.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Compras_81.xlsx',base64.encodestring(b''.join(f.readlines())))
			

	def get_excel_82(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Compras_82.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(2)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34',
					'CAMPO 35','CAMPO 36']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '0.00',formats['numberdos'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '0.00',formats['numberdos'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '0.00',formats['numberdos'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.0000',formats['numbercuatro'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '',formats['especial1'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '',formats['especial1'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '',formats['especial1'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '',formats['especial1'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '',formats['especial1'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '',formats['especial1'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '',formats['especial1'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '',formats['especial1'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			worksheet.write(x,34,line['campo35'] if line['campo35'] else '',formats['especial1'])
			worksheet.write(x,35,line['campo36'] if line['campo36'] else '',formats['especial1'])
			x+=1

		widths = [12,22,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Compras_82.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Compras_82.xlsx',base64.encodestring(b''.join(f.readlines())))

	
	def get_excel_141(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Registro_de_Ventas_141.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(3)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21','CAMPO 22','CAMPO 23',
					'CAMPO 24','CAMPO 25','CAMPO 26','CAMPO 27','CAMPO 28','CAMPO 29','CAMPO 30','CAMPO 31','CAMPO 32','CAMPO 33','CAMPO 34','CAMPO 35']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '0.00',formats['numberdos'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '0.00',formats['numberdos'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '0.00',formats['numberdos'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '0.00',formats['numberdos'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '0.00',formats['numberdos'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '0.00',formats['numberdos'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '0.00',formats['numberdos'])
			worksheet.write(x,21,line['campo22'] if line['campo22'] else '0.00',formats['numberdos'])
			worksheet.write(x,22,line['campo23'] if line['campo23'] else '0.00',formats['numberdos'])
			worksheet.write(x,23,line['campo24'] if line['campo24'] else '0.00',formats['numberdos'])
			worksheet.write(x,24,line['campo25'] if line['campo25'] else '0.00',formats['numberdos'])
			worksheet.write(x,25,line['campo26'] if line['campo26'] else '',formats['especial1'])
			worksheet.write(x,26,line['campo27'] if line['campo27'] else '0.00',formats['numbercuatro'])
			worksheet.write(x,27,line['campo28'] if line['campo28'] else '',formats['especial1'])
			worksheet.write(x,28,line['campo29'] if line['campo29'] else '',formats['especial1'])
			worksheet.write(x,29,line['campo30'] if line['campo30'] else '',formats['especial1'])
			worksheet.write(x,30,line['campo31'] if line['campo31'] else '',formats['especial1'])
			worksheet.write(x,31,line['campo32'] if line['campo32'] else '',formats['especial1'])
			worksheet.write(x,32,line['campo33'] if line['campo33'] else '',formats['especial1'])
			worksheet.write(x,33,line['campo34'] if line['campo34'] else '',formats['especial1'])
			worksheet.write(x,34,line['campo35'] if line['campo35'] else '',formats['especial1'])
			x+=1

		widths = [12,22,12,12,12,12,12,12,12,12,12,50,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Registro_de_Ventas_141.xlsx', 'rb')
		return self.env['popup.it'].get_file('Registro_de_Ventas_141.xlsx',base64.encodestring(b''.join(f.readlines())))


	def get_excel_diario(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Libro_Diario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(4)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '',formats['especial1'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			x+=1

		widths = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,42,12,12,12,30,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Libro_Diario.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Libro_Diario.xlsx',base64.encodestring(b''.join(f.readlines())))


	def get_excel_plan_c(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Plan_Contable.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(5)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			x+=1

		widths = [12,12,57,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Plan_Contable.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Plan_Contable.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_mayor(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Ple_Mayor.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(6)

		worksheet = workbook.add_worksheet(nomenclatura)
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11','CAMPO 12',
					'CAMPO 13','CAMPO 14','CAMPO 15','CAMPO 16','CAMPO 17','CAMPO 18','CAMPO 19','CAMPO 20','CAMPO 21']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['campo1'] if line['campo1'] else '',formats['especial1'])
			worksheet.write(x,1,line['campo2'] if line['campo2'] else '',formats['especial1'])
			worksheet.write(x,2,line['campo3'] if line['campo3'] else '',formats['especial1'])
			worksheet.write(x,3,line['campo4'] if line['campo4'] else '',formats['especial1'])
			worksheet.write(x,4,line['campo5'] if line['campo5'] else '',formats['especial1'])
			worksheet.write(x,5,line['campo6'] if line['campo6'] else '',formats['especial1'])
			worksheet.write(x,6,line['campo7'] if line['campo7'] else '',formats['especial1'])
			worksheet.write(x,7,line['campo8'] if line['campo8'] else '',formats['especial1'])
			worksheet.write(x,8,line['campo9'] if line['campo9'] else '',formats['especial1'])
			worksheet.write(x,9,line['campo10'] if line['campo10'] else '',formats['especial1'])
			worksheet.write(x,10,line['campo11'] if line['campo11'] else '',formats['especial1'])
			worksheet.write(x,11,line['campo12'] if line['campo12'] else '',formats['especial1'])
			worksheet.write(x,12,line['campo13'] if line['campo13'] else '',formats['especial1'])
			worksheet.write(x,13,line['campo14'] if line['campo14'] else '',formats['especial1'])
			worksheet.write(x,14,line['campo15'] if line['campo15'] else '',formats['especial1'])
			worksheet.write(x,15,line['campo16'] if line['campo16'] else '',formats['especial1'])
			worksheet.write(x,16,line['campo17'] if line['campo17'] else '',formats['especial1'])
			worksheet.write(x,17,line['campo18'] if line['campo18'] else '0.00',formats['numberdos'])
			worksheet.write(x,18,line['campo19'] if line['campo19'] else '0.00',formats['numberdos'])
			worksheet.write(x,19,line['campo20'] if line['campo20'] else '',formats['especial1'])
			worksheet.write(x,20,line['campo21'] if line['campo21'] else '',formats['especial1'])
			x+=1

		widths = [12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,42,12,12,12,28,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Ple_Mayor.xlsx', 'rb')
		return self.env['popup.it'].get_file('Ple_Mayor.xlsx',base64.encodestring(b''.join(f.readlines())))
		

	def get_excel_servidores(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Servidores.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(7)

		worksheet = workbook.add_worksheet("Servidores")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,line['apellido_p'] if line['apellido_p'] else '',formats['especial1'])
			worksheet.write(x,3,line['apellido_m'] if line['apellido_m'] else '',formats['especial1'])
			worksheet.write(x,4,line['namep'] if line['namep'] else '',formats['especial1'])
			worksheet.write(x,5,line['is_not_home'] if line['is_not_home'] else '',formats['especial1'])
			worksheet.write(x,6,line['c_d_imp'] if line['c_d_imp'] else '0',formats['especial1'])
			x+=1

		widths = [9,12,26,26,52,10,10]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Servidores.xlsx', 'rb')
		return self.env['popup.it'].get_file('Servidores.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_excel_recibos(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Recibos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		sql_ple,nomenclatura = self._get_sql(7)

		worksheet = workbook.add_worksheet("Recibos")
		worksheet.set_tab_color('blue')

		HEADERS = ['CAMPO 1','CAMPO 2','CAMPO 3','CAMPO 4','CAMPO 5','CAMPO 6','CAMPO 7','CAMPO 8','CAMPO 9','CAMPO 10','CAMPO 11']

		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		self.env.cr.execute(sql_ple)
		dicc = self.env.cr.dictfetchall()

		for line in dicc:
			worksheet.write(x,0,line['tdp'] if line['tdp'] else '',formats['especial1'])
			worksheet.write(x,1,line['docp'] if line['docp'] else '',formats['especial1'])
			worksheet.write(x,2,'R',formats['especial1'])
			worksheet.write(x,3,line['serie'] if line['serie'] else '',formats['especial1'])
			worksheet.write(x,4,line['numero'] if line['numero'] else '',formats['especial1'])
			worksheet.write(x,5,line['renta'] if line['renta'] else '0.00',formats['numberdos'])
			worksheet.write(x,6,line['fecha_e'] if line['fecha_e'] else '',formats['dateformat'])
			worksheet.write(x,7,line['fecha_p'] if line['fecha_p'] else '',formats['dateformat'])
			worksheet.write(x,8,'0' if line['retencion'] == 0 else '1',formats['especial1'])
			worksheet.write(x,9,'',formats['especial1'])
			worksheet.write(x,10,'',formats['especial1'])
			x+=1

		widths = [9,12,12,12,12,12,12,12,12,12,12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Recibos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Recibos.xlsx',base64.encodestring(b''.join(f.readlines())))

	def get_pdf_libro_diario(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_diariog(self):
			sql = """
				SELECT 
				vsd.libro,
				vsd.move_id,
				vsd.voucher,
				vsd.fecha,
				vsd.glosa,
				vsd.cuenta,
				aa.name as des,
				vsd.debe,
				vsd.haber
				FROM vst_diariog vsd
				LEFT JOIN account_account aa ON aa.id = vsd.account_id
				WHERE (vsd.fecha between '%s' and '%s')
				and vsd.company_id = %s
				order by vsd.libro,vsd.voucher
			
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** LIBRO DIARIO DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=6><b>N° CORREL. ASNTO COD. UNI. DE OPER.</b></font>",style), 
				Paragraph("<font size=6><b>FECHA DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=6><b>GLOSA O DESCRIPCION DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=6><b>CUENTA CONTABLE ASOCIADA A LA OPERACION</b></font>",style), 
				'', 
				Paragraph("<font size=6><b>MOVIMIENTO</b></font>",style), 
				''],
				['','','',Paragraph("<font size=6><b>CODIGO</b></font>",style),
				Paragraph("<font size=6><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=6><b>DEBE</b></font>",style),
				Paragraph("<font size=6><b>HABER</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(4,0)),
				('SPAN',(5,0),(6,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-85)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_diario_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [60,45,130,40,140,60,60]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-43

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_diariog(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		libro = ''
		voucher = ''
		sum_debe = 0
		sum_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 8)
			if cont == 0:
				libro = i['libro']
				voucher = i['voucher']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,libro)
				pos_inicial -= 15

			
			if libro != i['libro']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				sum_debe = 0
				sum_haber = 0
				pos_inicial -= 25

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				
				libro = i['libro']
				voucher = i['voucher']
				c.drawString( first_pos+2 ,pos_inicial,libro)
				pos_inicial -= 15

			if voucher != i['voucher']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				sum_debe = 0
				sum_haber = 0
				pos_inicial -= 15

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

				voucher = i['voucher']
				pos_inicial -= 10


			c.setFont("Helvetica", 6)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',130) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['des'] if i['des'] else '',150) )
			first_pos += size_widths[4]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DIARIO '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_libro_mayor(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_mayor(self):
			sql = """
				SELECT gmd.cuenta, aa.name AS name_cuenta,
				gmd.libro,gmd.td_sunat, gmd.nro_comprobante,
				gmd.voucher, 
				to_char(gmd.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
				gmd.glosa,
				gmd.debe, gmd.haber
				from get_mayor_detalle('%s','%s',%s) gmd
				LEFT JOIN account_account aa ON aa.code = gmd.cuenta AND aa.company_id = %s
			
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** LIBRO MAYOR DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=6><b>LIBRO</b></font>",style), 
				Paragraph("<font size=6><b>TD</b></font>",style), 
				Paragraph("<font size=6><b>NUMERO</b></font>",style), 
				Paragraph("<font size=6><b>NRO CORRELATIVO</b></font>",style), 
				Paragraph("<font size=6><b>FECHA</b></font>",style), 
				Paragraph("<font size=6><b>DESCRIPCION O GLOSA</b></font>",style),
				Paragraph("<font size=6><b>SALDOS Y MOVIMIENTOS</b></font>",style), 
				''],
				['','','','','','',
				Paragraph("<font size=6><b>DEUDOR</b></font>",style),
				Paragraph("<font size=6><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(3,1)),
				('SPAN',(4,0),(4,1)),
				('SPAN',(5,0),(5,1)),
				('SPAN',(6,0),(7,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-85)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_mayor_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [60,35,60,70,50,140,60,60]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-43

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_mayor(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 8)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cod. Cuenta: ' + cuenta + '' + i['name_cuenta'])
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTAL CUENTA:')
				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				pos_inicial -= 10

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 8)

				c.line(440,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

				c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
				pos_inicial -= 20

				c.line(440,pos_inicial+3,565,pos_inicial+3)

				sum_debe = 0
				sum_haber = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 8)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,'Cod. Cuenta: ' + cuenta + '' + i['name_cuenta'])
				pos_inicial -= 15


			c.setFont("Helvetica", 6)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['libro'] if i['libro'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',150) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[6]

			c.drawRightString( first_pos+60 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 8)
		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTAL CUENTA:')
		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 8)

		c.line(440,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 505,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
		pos_inicial -= 20

		c.line(440,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO MAYOR '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_compras(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_compras(self):
			sql = """
				SELECT 
				vc.voucher,
				to_char(vc.fecha_e::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_e,
				to_char(vc.fecha_v::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_v,
				vc.td,vc.serie,vc.anio,vc.numero,
				vc.tdp,vc.docp, vc.namep,
				coalesce(vc.base1,0) as base1,coalesce(vc.igv1,0) as igv1,
				coalesce(vc.base2,0) as base2,coalesce(vc.igv2,0) as igv2,
				coalesce(vc.base3,0) as base3,coalesce(vc.igv3,0) as igv3,
				coalesce(vc.cng,0) as cng,coalesce(vc.isc,0) as isc,coalesce(vc.otros,0) as otros,coalesce(vc.icbper,0) as icbper,coalesce(vc.total,0) as total,
				CASE
					WHEN rp.is_not_home = True THEN vc.numero ELSE ''
				END AS nro_no_dom,
				vc.comp_det,
				to_char(vc.fecha_det::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_det,
				vc.currency_rate,
				to_char(vc.f_doc_m::timestamp with time zone, 'yyyy/mm/dd'::text) as f_doc_m,
				vc.td_doc_m,vc.serie_m,vc.numero_m
				FROM vst_compras_1_1 vc
				LEFT JOIN res_partner rp ON rp.id = vc.partner_id
				WHERE (vc.fecha_cont BETWEEN '%s' AND '%s') AND vc.company = %s
				order by vc.td, vc.voucher
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** REGISTRO DE COMPRAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 4
			style.alignment= 1

			data= [[Paragraph("<font size=4.5><b>N° Vou.</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Emision</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Venc</b></font>",style), 
				Paragraph("<font size=4.5><b>Comprobante de pago</b></font>",style), 
				'', 
				'',
				Paragraph("<font size=4.5><b>Nº Comprobante Pago</b></font>",style), 
				Paragraph("<font size=4.5><b>Informacion del Proveedor</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. Grav. y/o Exp.</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. Grav. y/o Exp. y a Oper.</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Adq. Grav. dest. a Oper. No Gravadas</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Valor de Adq no Gravadas</b></font>",style),
				Paragraph("<font size=4.5><b>I.S.C.</b></font>",style),
				Paragraph("<font size=4.5><b>ICBPER</b></font>",style),
				Paragraph("<font size=4.5><b>Otros Tributos</b></font>",style),
				Paragraph("<font size=4.5><b>Importe Total</b></font>",style),
				Paragraph("<font size=4.5><b>Nº Comp. de pago emitido por sujeto no domiciliado </b></font>",style),
				Paragraph("<font size=4.5><b>Constancia de Deposito de Detracción</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>T.C.</b></font>",style),
				Paragraph("<font size=4.5><b>Referencia del Documento</b></font>",style),
				'','',''],
				['','','',
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Año de Emision DUA o DSI</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Doc. de Identidad</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Apellidos y nombres o Razon Social</b></font>",style),
				'','','','','','','','','','','','','','','',
				Paragraph("<font size=4.5><b>Fecha</b></font>",style),
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero Comprobante Doc Numero de pago</b></font>",style)],
				['','','','','','','',
				Paragraph("<font size=4.5><b>Doc</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V.</b></font>",style),
				'','','','','','',
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				Paragraph("<font size=4.5><b>Fecha Emi.</b></font>",style),
				'','','','',''
				]]
			t=Table(data,colWidths=size_widths, rowHeights=(14))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,2)),
				('SPAN',(1,0),(1,2)),
				('SPAN',(2,0),(2,2)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(4,2)),
				('SPAN',(5,1),(5,2)),
				('SPAN',(6,0),(6,2)),
				('SPAN',(7,0),(9,0)),
				('SPAN',(7,1),(8,1)),
				('SPAN',(9,1),(9,2)),
				('SPAN',(10,0),(11,1)),
				('SPAN',(12,0),(13,1)),
				('SPAN',(14,0),(15,1)),
				('SPAN',(16,0),(16,2)),
				('SPAN',(17,0),(17,2)),
				('SPAN',(18,0),(18,2)),
				('SPAN',(19,0),(19,2)),
				('SPAN',(20,0),(20,2)),
				('SPAN',(21,0),(21,2)),
				('SPAN',(22,0),(23,1)),
				('SPAN',(24,0),(24,2)),
				('SPAN',(25,0),(28,0)),
				('SPAN',(25,1),(25,2)),
				('SPAN',(26,1),(26,2)),
				('SPAN',(27,1),(27,2)),
				('SPAN',(28,1),(28,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "compra_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [30,28,28,14,16,25,32,15,30,67,29,29,27,25,25,26,24,23,24,24,34,38,29,30,20,25,14,18,45]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 4)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_compras(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		td = ''
		base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_base1, total_base2, total_base3, total_igv1, total_igv2, total_igv3, total_cng, total_isc, total_icbper, total_otros, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 4)
			if cont == 0:
				td = i['td']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + td )
				pos_inicial -= 10

			if td != i['td']:
				c.line(314,pos_inicial+3,598,pos_inicial+3)
				c.drawString( 270 ,pos_inicial-5,'TOTALES:')
				c.drawRightString( 342,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)) )
				c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)))
				c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)))
				c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)))
				c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)))
				c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)))
				c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)))
				c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)))
				c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
				c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)))
				c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

				base1, base2, base3, igv1, igv2, igv3, cng, isc, otros, icbper, total = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 4)

				td = i['td']
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + td )
				pos_inicial -= 10


			c.setFont("Helvetica", 4)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_e'] if i['fecha_e'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_v'] if i['fecha_v'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td'] if i['td'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie'] if i['serie'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['anio'] if i['anio'] else '',50) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero'] if i['numero'] else '',50) )
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['tdp'] if i['tdp'] else '',50) )
			first_pos += size_widths[7]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['docp'] if i['docp'] else '',50) )
			first_pos += size_widths[8]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['namep'] if i['namep'] else '',130) )
			first_pos += size_widths[9]

			c.drawRightString( 342 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base1'])) )
			base1 += i['base1']
			total_base1 += i['base1']
			first_pos += size_widths[10]

			c.drawRightString( 371 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv1'])) )
			igv1 += i['igv1']
			total_igv1 += i['igv1']
			first_pos += size_widths[11]

			c.drawRightString( 400 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base2'])) )
			base2 += i['base2']
			total_base2 += i['base2']
			first_pos += size_widths[12]

			c.drawRightString( 427 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv2'])) )
			igv2 += i['igv2']
			total_igv2 += i['igv2']
			first_pos += size_widths[13]

			c.drawRightString( 452 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['base3'])) )
			base3 += i['base3']
			total_base3 += i['base3']
			first_pos += size_widths[14]

			c.drawRightString( 477 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv3'])) )
			igv3 += i['igv3']
			total_igv3 += i['igv3']
			first_pos += size_widths[15]

			c.drawRightString( 503 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['cng'])) )
			cng += i['cng']
			total_cng += i['cng']
			first_pos += size_widths[16]

			c.drawRightString( 527 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc'])) )
			isc += i['isc']
			total_isc += i['isc']
			first_pos += size_widths[17]

			c.drawRightString( 550 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])) )
			icbper += i['icbper']
			total_icbper += i['icbper']
			first_pos += size_widths[18]

			c.drawRightString( 574 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros'])) )
			otros += i['otros']
			total_otros += i['otros']
			first_pos += size_widths[19]

			c.drawRightString( 598 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])) )
			total += i['total']
			total_total += i['total']
			first_pos += size_widths[20]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_no_dom'] if i['nro_no_dom'] else '',50) )
			first_pos += size_widths[21]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['comp_det'] if i['comp_det'] else '',50) )
			first_pos += size_widths[22]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_det'] if i['fecha_det'] else '',50) )
			first_pos += size_widths[23]

			c.drawRightString( first_pos+18 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])) )
			first_pos += size_widths[24]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['f_doc_m'] if i['f_doc_m'] else '',50) )
			first_pos += size_widths[25]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_doc_m'] if i['td_doc_m'] else '',50) )
			first_pos += size_widths[26]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie_m'] if i['serie_m'] else '',50) )
			first_pos += size_widths[27]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero_m'] if i['numero_m'] else '',50) )

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 4)
		c.line(314,pos_inicial+3,598,pos_inicial+3)
		c.drawString( 270 ,pos_inicial-5,'TOTALES:')
		c.drawRightString( 342 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base1)) )
		c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv1)))
		c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base2)))
		c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv2)))
		c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % base3)))
		c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv3)))
		c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % cng)))
		c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc)))
		c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
		c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros)))
		c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 4)

		c.line(314,pos_inicial+3,598,pos_inicial+3)

		c.drawString( 270 ,pos_inicial-5,'TOTAL GENERAL:')
		c.drawRightString( 342 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base1)) )
		c.drawRightString( 371 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv1)))
		c.drawRightString( 400 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base2)))
		c.drawRightString( 427 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv2)))
		c.drawRightString( 452 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_base3)))
		c.drawRightString( 477 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv3)))
		c.drawRightString( 503 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_cng)))
		c.drawRightString( 527 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc)))
		c.drawRightString( 550 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)))
		c.drawRightString( 574 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros)))
		c.drawRightString( 598 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)))

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.line(314,pos_inicial+3,598,pos_inicial+3)	

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('REGISTRO DE COMPRAS '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_ventas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_ventas(self):
			sql = """
				SELECT vst.voucher,
				to_char(vst.fecha_e::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_e,
				to_char(vst.fecha_v::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_v,
				vst.td,
				vst.serie,
				vst.numero,
				vst.tdp,
				vst.docp,
				vst.namep,
				vst.exp,
				vst.venta_g,
				vst.exo,
				vst.inaf,
				vst.isc_v,
				vst.igv_v,
				vst.otros_v,
				vst.icbper,
				vst.total,
				vst.currency_rate,
				to_char(vst.f_doc_m::timestamp with time zone, 'yyyy/mm/dd'::text) as f_doc_m,
				vst.td_doc_m,
				vst.serie_m,
				vst.numero_m
				FROM vst_ventas_1_1 vst
				WHERE (vst.fecha_cont BETWEEN '%s' AND '%s') 
				AND vst.company = %s
				ORDER BY vst.td, vst.serie, vst.numero
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal-12, "*** REGISTRO DE VENTAS E INGRESOS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-10,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-20, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-30, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 4
			style.alignment= 1

			data= [[Paragraph("<font size=4.5><b>N° Vou.</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Emision</b></font>",style), 
				Paragraph("<font size=4.5><b>F. Venc</b></font>",style), 
				Paragraph("<font size=4.5><b>Comprobante de pago</b></font>",style), 
				'', 
				'',
				Paragraph("<font size=4.5><b>Informacion del Cliente</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Valor Facturado de la Exportacion</b></font>",style),
				Paragraph("<font size=4.5><b>Base Imp. de la Ope. Gravada</b></font>",style),
				Paragraph("<font size=4.5><b>Imp. Total de la Operacion</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>I.S.C.</b></font>",style),
				Paragraph("<font size=4.5><b>I.G.V. y/o IPM</b></font>",style),
				Paragraph("<font size=4.5><b>ICBPER</b></font>",style),
				Paragraph("<font size=4.5><b>Otros Tributos y cargos que no forman parte de la base imponible</b></font>",style),
				Paragraph("<font size=4.5><b>Importe Total</b></font>",style),
				Paragraph("<font size=4.5><b>T.C.</b></font>",style),
				Paragraph("<font size=4.5><b>Referencia del Comprobante</b></font>",style),
				'','',''],
				['','','',
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				Paragraph("<font size=4.5><b>Doc. de Identidad</b></font>",style),
				'',
				Paragraph("<font size=4.5><b>Apellidos y nombres o Razon Social</b></font>",style),
				'','',
				Paragraph("<font size=4.5><b>Exonerada</b></font>",style),
				Paragraph("<font size=4.5><b>Inafecta</b></font>",style),
				'','','','','','',
				Paragraph("<font size=4.5><b>Fecha</b></font>",style),
				Paragraph("<font size=4.5><b>T/D</b></font>",style),
				Paragraph("<font size=4.5><b>Serie</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style)],
				['','','','','','',
				Paragraph("<font size=4.5><b>Doc</b></font>",style),
				Paragraph("<font size=4.5><b>Numero</b></font>",style),
				'','','','','','','','','','','','','','','']]
			t=Table(data,colWidths=size_widths, rowHeights=(14))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,2)),
				('SPAN',(1,0),(1,2)),
				('SPAN',(2,0),(2,2)),
				('SPAN',(3,0),(5,0)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(4,2)),
				('SPAN',(5,1),(5,2)),
				('SPAN',(6,0),(8,0)),
				('SPAN',(6,1),(7,1)),
				('SPAN',(8,1),(8,2)),
				('SPAN',(9,0),(9,2)),
				('SPAN',(10,0),(10,2)),
				('SPAN',(11,0),(12,0)),
				('SPAN',(11,1),(11,2)),
				('SPAN',(12,1),(12,2)),
				('SPAN',(13,0),(13,2)),
				('SPAN',(14,0),(14,2)),
				('SPAN',(15,0),(15,2)),
				('SPAN',(16,0),(16,2)),
				('SPAN',(17,0),(17,2)),
				('SPAN',(18,0),(18,2)),
				('SPAN',(19,0),(22,0)),
				('SPAN',(19,1),(19,2)),
				('SPAN',(20,1),(20,2)),
				('SPAN',(21,1),(21,2)),
				('SPAN',(22,1),(22,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "venta_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [32,28,28,14,18,32,15,33,100,40,40,30,30,40,40,40,40,40,20,28,14,18,45]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 4)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_ventas(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		td = ''
		exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0
		total_exp, total_venta_g, total_exo, total_inaf, total_isc_v, total_igv_v, total_icbper, total_otros_v, total_total = 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 4)
			if cont == 0:
				td = i['td']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + td )
				pos_inicial -= 10

			if td != i['td']:
				c.line(330,pos_inicial+3,667,pos_inicial+3)
				c.drawString( 280 ,pos_inicial-5,'TOTALES:')
				c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)) )
				c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)))
				c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)))
				c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)))
				c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)))
				c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)))
				c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
				c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)))
				c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))

				exp, venta_g, exo, inaf, isc_v, igv_v, icbper, otros_v, total = 0, 0, 0, 0, 0, 0, 0, 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 4)

				td = i['td']
				c.drawString( first_pos+2 ,pos_inicial,'Tipo Doc.: ' + td )
				pos_inicial -= 10


			c.setFont("Helvetica", 4)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_e'] if i['fecha_e'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_v'] if i['fecha_v'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td'] if i['td'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie'] if i['serie'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero'] if i['numero'] else '',50) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['tdp'] if i['tdp'] else '',50) )
			first_pos += size_widths[6]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['docp'] if i['docp'] else '',50) )
			first_pos += size_widths[7]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['namep'] if i['namep'] else '',190) )
			first_pos += size_widths[8]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exp'])) )
			exp += i['exp']
			total_exp += i['exp']
			first_pos += size_widths[9]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['venta_g'])) )
			venta_g += i['venta_g']
			total_venta_g += i['venta_g']
			first_pos += size_widths[10]

			c.drawRightString( first_pos+27 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['exo'])) )
			exo += i['exo']
			total_exo += i['exo']
			first_pos += size_widths[11]

			c.drawRightString( first_pos+27 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['inaf'])) )
			inaf += i['inaf']
			total_inaf += i['inaf']
			first_pos += size_widths[12]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['isc_v'])) )
			isc_v += i['isc_v']
			total_isc_v += i['isc_v']
			first_pos += size_widths[13]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['igv_v'])) )
			igv_v += i['igv_v']
			total_igv_v += i['igv_v']
			first_pos += size_widths[14]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['icbper'])) )
			icbper += i['icbper']
			total_icbper += i['icbper']
			first_pos += size_widths[15]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['otros_v'])) )
			otros_v += i['otros_v']
			total_otros_v += i['otros_v']
			first_pos += size_widths[16]

			c.drawRightString( first_pos+37 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['total'])) )
			total += i['total']
			total_total += i['total']
			first_pos += size_widths[17]

			c.drawRightString( first_pos+17 ,pos_inicial,'{:,.4f}'.format(decimal.Decimal ("%0.4f" % i['currency_rate'])) )
			first_pos += size_widths[18]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['f_doc_m'] if i['f_doc_m'] else '',50) )
			first_pos += size_widths[19]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_doc_m'] if i['td_doc_m'] else '',50) )
			first_pos += size_widths[20]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['serie_m'] if i['serie_m'] else '',50) )
			first_pos += size_widths[21]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['numero_m'] if i['numero_m'] else '',50) )

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 4)
		c.line(330,pos_inicial+3,667,pos_inicial+3)
		c.drawString( 280 ,pos_inicial-5,'TOTALES:')
		c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exp)) )
		c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % venta_g)))
		c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % exo)))
		c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % inaf)))
		c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % isc_v)))
		c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % igv_v)))
		c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % icbper)))
		c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % otros_v)))
		c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total)))
		
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 4)

		c.line(330,pos_inicial+3,667,pos_inicial+3)

		c.drawString( 280 ,pos_inicial-5,'TOTAL GENERAL:')
		c.drawRightString( 367 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exp)) )
		c.drawRightString( 407 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_venta_g)))
		c.drawRightString( 437 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_exo)))
		c.drawRightString( 467 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_inaf)))
		c.drawRightString( 507 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_isc_v)))
		c.drawRightString( 547 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_igv_v)))
		c.drawRightString( 587 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_icbper)))
		c.drawRightString( 627 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_otros_v)))
		c.drawRightString( 667 ,pos_inicial-5,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % total_total)))

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.line(330,pos_inicial+3,667,pos_inicial+3)	

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('REGISTRO DE VENTAS  '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_libro_caja(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_caja(self):
			sql = """
				SELECT 
				gc.cuenta,
				aa.name as name_cuenta,
				gc.voucher,
				to_char(gc.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
				gc.glosa,
				gc.debe,
				gc.haber
				FROM get_caja_bancos('%s','%s',%s) gc
				LEFT JOIN account_account aa ON aa.id = gc.account_id
				WHERE LEFT(gc.cuenta,3) = '101'
			
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

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
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO CAJA - MOVIMIENTOS DEL EFECTIVO DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>NUMERO DE VOUCHER</b></font>",style), 
				Paragraph("<font size=8><b>FECHA DE OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>DESCRIPCION DE LA OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>SALDOS Y MOVIMIENTOS</b></font>",style),
				''],
				['','','',
				Paragraph("<font size=8><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(4,0)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "libro_caja.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [80,80,235,70,70]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_caja(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		cuenta = ''
		sum_debe = 0
		sum_haber = 0
		saldo_debe = 0
		saldo_haber = 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 10)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'])
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.setFont("Helvetica-Bold", 9)
				c.line(425,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'TOTALES:')
				c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
				pos_inicial -= 10

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				c.line(425,pos_inicial+3,565,pos_inicial+3)
				c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
				saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
				saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

				c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
				c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
				pos_inicial -= 20

				c.line(425,pos_inicial+3,565,pos_inicial+3)

				sum_debe = 0
				sum_haber = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 10)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,'Cuenta: ' + cuenta + ' ' + i['name_cuenta'])
				pos_inicial -= 15


			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',150) )
			first_pos += size_widths[2]

			c.drawRightString( first_pos+70 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			sum_debe += i['debe']
			first_pos += size_widths[3]

			c.drawRightString( first_pos+70 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])))
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(425,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(425,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 350 ,pos_inicial-10,'SALDO FINAL:')
		saldo_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		saldo_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 495,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_debe)) )
		c.drawRightString( 565 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_haber)))
		pos_inicial -= 20

		c.line(425,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO CAJA '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_libro_banco(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_banco(self):
			sql = """
				SELECT 		
				aa.code_bank,	
				aa.account_number,
				gb.cuenta,
				aa.name as nombre_cuenta,
				gb.libro,
				gb.voucher,
				to_char(gb.fecha::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha,
				eip.code as medio_pago,
				gb.glosa,
				gb.partner,
				gb.nro_comprobante,
				gb.debe,
				gb.haber		
				FROM get_bancos('%s','%s',%s) gb
				LEFT JOIN account_move am ON am.id = gb.move_id
				LEFT JOIN account_account aa ON aa.id = gb.account_id		
				LEFT JOIN einvoice_catalog_payment eip ON eip.id = am.td_payment_id		
				ORDER BY gb.cuenta,gb.fecha	
			
			""" % (self.period.date_start.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO BANCOS - MOVIMIENTOS DE LA CUENTA CORRIENTE DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=7.5><b>N° VOU.</b></font>",style), 
				Paragraph("<font size=7.5><b>N° CORRELATIVO DEL LIBRO DIARIO</b></font>",style), 
				Paragraph("<font size=7.5><b>FECHA OPERACION</b></font>",style), 
				Paragraph("<font size=8><b>OPERACIONES BANCARIAS</b></font>",style),
				'', 
				'',
				'',
				Paragraph("<font size=8><b>SALDOS Y MOVIMIENTOS</b></font>",style),
				''],
				['','','',
				Paragraph("<font size=7.5>MEDIO DE PAGO</font>",style),
				Paragraph("<font size=7.5>DESC. OPERACION</font>",style),
				Paragraph("<font size=7.5>APELLIDOS Y NOMBRES, DENOMINACION O RAZON SOCIAL</font>",style),
				Paragraph("<font size=7>N. TRANSACCIÓN BANCARIA DE DOCUMENTOS O DE CONTROL INTERNO DE LA OPERACIÓN</font>",style),
				Paragraph("<font size=7.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=7.5><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[18,30])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(0,1)),
				('SPAN',(1,0),(1,1)),
				('SPAN',(2,0),(2,1)),
				('SPAN',(3,0),(6,0)),
				('SPAN',(7,0),(8,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "banco_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [45,55,55,55,150,140,120,85,85]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_banco(self))
		res = self.env.cr.dictfetchall()
		
		cont = 0
		cuenta = ''
		debe, haber, sum_debe, sum_haber, final_debe, final_haber = 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30
			
			c.setFont("Helvetica-Bold", 7)
			if cont == 0:
				cuenta = i['cuenta']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,i['cuenta'])
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+50 ,pos_inicial,i['nombre_cuenta'])
				c.setFont("Helvetica-Bold", 6)
				c.drawString( first_pos+100 ,pos_inicial,'Cod. Ent. Financiera:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+170 ,pos_inicial,i['code_bank'] if i['code_bank'] else '')
				c.setFont("Helvetica-Bold", 6)
				c.drawString( first_pos+400 ,pos_inicial,'Número de cuenta:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+470 ,pos_inicial,i['account_number'] if i['account_number'] else '')
				pos_inicial -= 15

			if cuenta != i['cuenta']:
				c.line(655,pos_inicial+3,815,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'SUB TOTAL:')
				c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
				c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))

				debe, haber = 0, 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 7)

				cuenta = i['cuenta']
				c.drawString( first_pos+2 ,pos_inicial,i['cuenta'])
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+50 ,pos_inicial,i['nombre_cuenta'])
				c.setFont("Helvetica-Bold", 7)
				c.drawString( first_pos+100 ,pos_inicial,'Cod. Ent. Financiera:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+170 ,pos_inicial,i['code_bank'] if i['code_bank'] else '')
				c.setFont("Helvetica-Bold", 7)
				c.drawString( first_pos+400 ,pos_inicial,'Número de cuenta:')
				c.setFont("Helvetica", 7)
				c.drawString( first_pos+470 ,pos_inicial,i['account_number'] if i['account_number'] else '')
				pos_inicial -= 10


			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['libro'] if i['libro'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['voucher'] if i['voucher'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha'] if i['fecha'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['medio_pago'] if i['medio_pago'] else '',50) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['glosa'] if i['glosa'] else '',130) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',120) )
			first_pos += size_widths[5]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',50) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+82 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			sum_debe += i['debe']
			first_pos += size_widths[7]

			c.drawRightString( first_pos+82 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']
			sum_haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 7)
		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SUB TOTAL:')
		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % sum_haber)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(655,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		final_debe = (sum_debe - sum_haber) if sum_debe > sum_haber else 0
		final_haber = 0 if sum_debe > sum_haber else (sum_haber - sum_debe)

		c.drawRightString( 730,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_debe)) )
		c.drawRightString( 815 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_haber)))
		pos_inicial -= 20

		c.line(655,pos_inicial+3,815,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO BANCOS '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_inventario_balance(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_inventario(self):
			sql = """
				SELECT 
				cuenta,
				nomenclatura,
				debe_inicial,
				haber_inicial,
				debe,
				haber,
				saldo_deudor,
				saldo_acreedor,
				activo,
				pasivo,
				perdifun,
				gananfun
				FROM get_f2_register('%s',%s,'pen')
			
			""" % (self.period.code,
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO INVENTARIO Y BALANCE - BALANCE DE COMPROBACION DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUBCUENTA CONTABLE</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS INICIALES</b></font>",style),'',
				Paragraph("<font size=9><b>MOVIMIENTOS</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS FINALES</b></font>",style),'',
				Paragraph("<font size=9><b>SALDOS FINALES DEL BALANCE GENERAL</b></font>",style),'',
				Paragraph("<font size=9><b>PERDIDAS FINALES EST. DE PERDIDAS Y GANAN. POR FUNCION</b></font>",style),''],
				[Paragraph("<font size=9><b>CUENTA</b></font>",style),
				Paragraph("<font size=8.5><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=8.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACREEDOR</b></font>",style),
				Paragraph("<font size=8.5><b>DEBE</b></font>",style),
				Paragraph("<font size=8.5><b>HABER</b></font>",style),
				Paragraph("<font size=8.5><b>DEUDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACREEDOR</b></font>",style),
				Paragraph("<font size=8.5><b>ACTIVO</b></font>",style),
				Paragraph("<font size=8.5><b>PASIVO</b></font>",style),
				Paragraph("<font size=8.5><b>PERDIDA</b></font>",style),
				Paragraph("<font size=8.5><b>GANANCIA</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[30,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(3,0)),
				('SPAN',(4,0),(5,0)),
				('SPAN',(6,0),(7,0)),
				('SPAN',(8,0),(9,0)),
				('SPAN',(10,0),(11,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "inv_rep.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [48,185,55,55,55,55,55,55,55,55,55,55]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-60

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_inventario(self))
		res = self.env.cr.dictfetchall()

		debe_inicial, haber_inicial, debe, haber, saldo_deudor, saldo_acreedor, activo, pasivo, perdifun, gananfun = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',200) )
			first_pos += size_widths[1]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe_inicial'])) )
			debe_inicial += i['debe_inicial']
			first_pos += size_widths[2]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber_inicial'])) )
			haber_inicial += i['haber_inicial']
			first_pos += size_widths[3]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			first_pos += size_widths[4]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_deudor'])) )
			saldo_deudor += i['saldo_deudor']
			first_pos += size_widths[6]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_acreedor'])) )
			saldo_acreedor += i['saldo_acreedor']
			first_pos += size_widths[7]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['activo'])) )
			activo += i['activo']
			first_pos += size_widths[8]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['pasivo'])) )
			pasivo += i['pasivo']
			first_pos += size_widths[9]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['perdifun'])) )
			perdifun += i['perdifun']
			first_pos += size_widths[10]

			c.drawRightString( first_pos+53 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['gananfun'])) )
			gananfun += i['gananfun']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 7)
		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 316,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe_inicial)) )
		c.drawRightString( 371,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber_inicial)) )
		c.drawRightString( 426,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)) )
		c.drawRightString( 481 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))
		c.drawRightString( 536 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_deudor)))
		c.drawRightString( 591 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_acreedor)))
		c.drawRightString( 646 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % activo)))
		c.drawRightString( 701 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % pasivo)))
		c.drawRightString( 756 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % perdifun)))
		c.drawRightString( 811 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % gananfun)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'GANANCIA DEL EJERCICIO:')
		final_activo = abs(activo - pasivo) if (activo - pasivo) < 0 else 0
		final_pasivo = (activo - pasivo) if (activo - pasivo) > 0 else 0
		c.drawRightString( 646,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_activo)) )
		c.drawRightString( 701 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_pasivo)))
		final_perdifun = abs(perdifun - gananfun) if (perdifun - gananfun) < 0 else 0
		final_gananfun = (perdifun - gananfun) if (perdifun - gananfun) > 0 else 0
		c.drawRightString( 756 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_perdifun)))
		c.drawRightString( 811 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_gananfun)))
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 7)

		c.line(80,pos_inicial+3,815,pos_inicial+3)
		c.drawString( 80 ,pos_inicial-10,'SUMAS IGUALES:')

		c.drawRightString( 646,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_activo + activo))) )
		c.drawRightString( 701,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_pasivo + pasivo))) )
		c.drawRightString( 756,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_perdifun + perdifun))) )
		c.drawRightString( 811,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % (final_gananfun + gananfun))) )
		pos_inicial -= 20

		c.line(80,pos_inicial+3,815,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO INVENTARIO Y BALANCE '+ self.period.name,base64.encodestring(b''.join(f.readlines())))


	def get_pdf_10_caja_bancos(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_10_caja_bancos(self):
			sql = """
				SELECT 
				cuenta,
				nomenclatura,
				code_bank,
				account_number,
				moneda,
				debe,
				haber
				FROM get_detalle_pdf_10(%s,%s,%s)
			
			""" % (self.period.code[:4]+'00',
				self.period.code,
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 10 - CAJA Y BANCOS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA CONTABLE DIVISIONARIA</b></font>",style),'',
				Paragraph("<font size=9><b>REFERENCIA DE LA CUENTA</b></font>",style),'','',
				Paragraph("<font size=9><b>SALDO CONTABLE FINAL</b></font>",style),''],
				[Paragraph("<font size=9><b>CODIGO</b></font>",style),
				Paragraph("<font size=9><b>DENOMINACION</b></font>",style),
				Paragraph("<font size=9><b>ENT. FINANCIERA</b></font>",style),
				Paragraph("<font size=9><b>NUMERO DE CTA</b></font>",style),
				Paragraph("<font size=9><b>MONEDA</b></font>",style),
				Paragraph("<font size=9><b>DEUDOR</b></font>",style),
				Paragraph("<font size=9><b>ACREEDOR</b></font>",style)]]
			t=Table(data,colWidths=size_widths, rowHeights=[30,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(4,0)),
				('SPAN',(5,0),(6,0)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_10.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,200,100,150,50,100,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica", 7)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_10_caja_bancos(self))
		res = self.env.cr.dictfetchall()

		debe, haber = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 9)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',215) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['code_bank'] if i['code_bank'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['account_number'] if i['account_number'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,str(i['moneda']) if i['moneda'] else '')
			first_pos += size_widths[4]

			c.drawRightString( first_pos+100 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['debe'])) )
			debe += i['debe']
			first_pos += size_widths[5]

			c.drawRightString( first_pos+100 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['haber'])) )
			haber += i['haber']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(585,pos_inicial+3,780,pos_inicial+3)
		c.drawString( 500 ,pos_inicial-10,'TOTALES:')
		c.drawRightString( 680 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % debe)))
		c.drawRightString( 780 ,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % haber)))

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 10  '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_12_cliente(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_12_cliente(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '12'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 12 - CLIENTES DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL CLIENTE</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA2)</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_12.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_12_cliente(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 12 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_13_cobrar_relacionadas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_13_cobrar_relacionadas(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '13'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 13 - RELACIONADAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL CLIENTE</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO (TABLA2)</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_13.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_13_cobrar_relacionadas(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 13 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_14_cobrar_acc_personal(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_14_cobrar_acc_personal(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '14'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 14 - CTAS x COB. A ACCIONISTAS Y PERSONAL DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACIÓN DEL ACCIONISTA, SOCIO O PERSONAL</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE INICIO DE LA OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_14.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_14_cobrar_acc_personal(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 14 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_16_cobrar_diversas(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_16_cobrar_diversas(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '16'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 11)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 16 - CTAS x COB. DIVERSAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DE TERCEROS</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION COMP.DE PAGO O F. INICIO OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_16.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_16_cobrar_diversas(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 16 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_19_cobrar_dudosa(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_19_cobrar_dudosa(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '19'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 19 - PROVISION PARA CTAS DE COBRANZA DUDOSA DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DE DEUDORES</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION COMP.DE PAGO O F. INICIO OPERACION</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-110
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "caja_19.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_19_cobrar_dudosa(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 19 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_40(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_40(self):
			sql = """
				SELECT
				cuenta,
				nomenclatura,
				debe-haber AS saldo
				FROM get_f1_register('%s','%s',%s,'pen')
				WHERE left(cuenta,2) = '40'
			
			""" % (self.period.code[:4]+'00',
				self.period.code,
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 8)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 - TRIBUTOS POR PAGAR DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUB CUENTA TRIBUTOS POR PAGAR</b></font>",style),'', 
				Paragraph("<font size=8><b>SALDO FINAL</b></font>",style)],
				[Paragraph("<font size=8><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>DENOMINACION</b></font>",style),'']]
			t=Table(data,colWidths=size_widths, rowHeights=(20))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,0)),
				('SPAN',(2,0),(2,1)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,70,500) 
			t.drawOn(c,70,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width - 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_40.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [80,300,80]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_40(self))
		res = self.env.cr.dictfetchall()

		saldo = 0

		for i in res:
			first_pos = 70

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',250) )
			first_pos += size_widths[1]

			c.drawRightString( first_pos+80 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])))
			saldo += i['saldo']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(450,pos_inicial+3,530,pos_inicial+3)
		c.drawString( 390 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 530,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)) )
		pos_inicial -= 20

		c.line(450,pos_inicial+3,530,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 40 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))


	def get_pdf_cuenta_41(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_41(self):
			sql = """
				SELECT
				gs.cuenta,
				aa.name AS nomenclatura,
				rp.ref,
				partner,
				td_partner,
				gs.doc_partner,
				SUM(saldo_mn) AS saldo
				FROM get_saldos('%s','%s',%s,1) gs
				LEFT JOIN account_account aa ON aa.id = gs.account_id
				LEFT JOIN res_partner rp ON rp.id = gs.partner_id
				WHERE LEFT(gs.cuenta,2) = '41'
				GROUP BY gs.cuenta,aa.name,rp.ref,partner,td_partner,gs.doc_partner
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 8)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 - REMUNERACIONES POR PAGAR DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-12, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-22,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-32, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-42, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=9><b>CUENTA Y SUBCUENTA REMUNERACIONES POR PAGAR</b></font>",style),'', 
				Paragraph("<font size=8><b>TRABAJADOR</b></font>",style),'','','',
				Paragraph("<font size=8><b>SALDO FINAL</b></font>",style)],
				['','',
				Paragraph("<font size=8><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES</b></font>",style),
				Paragraph("<font size=8><b>DOC DE IDENT.</b></font>",style),'',''],
				[Paragraph("<font size=7.5><b>CODIGO</b></font>",style),
				Paragraph("<font size=8><b>DENOMINACION</b></font>",style),'','',
				Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),'']]
			t=Table(data,colWidths=size_widths, rowHeights=(16))
			t.setStyle(TableStyle([
				('SPAN',(0,0),(1,1)),
				('SPAN',(2,0),(5,0)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,1),(3,2)),
				('SPAN',(4,1),(5,1)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1, colors.black),
				('ALIGN',(0,0),(-1,-1),'LEFT'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-95
			else:
				return pagina,posactual-valor

		width ,height  = A4  # 595 , 842
		wReal = width - 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_40.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= A4 )
		pos_inicial = hReal-50
		pagina = 1

		size_widths = [44,160,50,150,31,50,50]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-55

		c.setFont("Helvetica", 8)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_41(self))
		res = self.env.cr.dictfetchall()

		saldo = 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica", 7)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['cuenta'] if i['cuenta'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nomenclatura'] if i['nomenclatura'] else '',180) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['ref'] if i['ref'] else '',50) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',150) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[5]

			c.drawRightString( first_pos+50 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo'])))
			saldo += i['saldo']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold", 9)
		c.line(515,pos_inicial+3,565,pos_inicial+3)
		c.drawString( 470 ,pos_inicial-10,'TOTAL:')
		c.drawRightString( 565,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo)) )
		pos_inicial -= 20

		c.line(515,pos_inicial+3,565,pos_inicial+3)

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 41 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_42(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_42(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '42'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 42 - CTAS POR PAGAR COMERCIALES TERCEROS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_42.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_42(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 42 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_43(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_43(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '43'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 43 - CTAS POR PAGAR COMERCIALES RELACIONADAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_43.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_43(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 43 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_44(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_44(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '44'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 44 - CTAS POR PAGAR ACCIONISTAS Y DIRECTORES DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_44.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_44(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 44 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_45(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_45(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '45'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 45 - OBLIGACIONES FINANCIERAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_45.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_45(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 45 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_46(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_46(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '46'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 46 - CTAS POR PAGAR DIVERSAS TERCEROS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_46.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_46(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 46 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_47(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_47(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '47'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 47 - CTAS POR PAGAR DIVERSAS RELACIONADAS DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_47.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_47(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 47 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_48(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_48(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '48'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 12)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 48 - PROVISIONES DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_48.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_48(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 48 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))

	def get_pdf_cuenta_49(self):
		import importlib
		import sys
		importlib.reload(sys)

		def _get_sql_vst_49(self):
			sql = """
				SELECT 
				td_partner,
				doc_partner,
				partner,
				td_sunat,
				nro_comprobante,
				to_char(fecha_doc::timestamp with time zone, 'yyyy/mm/dd'::text) as fecha_doc,
				saldo_mn
				FROM get_saldos('%s','%s',%s,1)
				WHERE LEFT(cuenta,2) = '49'
			
			""" % (self.period.fiscal_year_id.date_from.strftime('%Y/%m/%d'),
				self.period.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id))

			return sql

		def particionar_text(c,tam):
			tet = ""
			for i in range(len(c)):
				tet += c[i]
				lines = simpleSplit(tet,'Helvetica',8,tam)
				if len(lines)>1:
					return tet[:-1]
			return tet

		def pdf_header(self,c,wReal,hReal,size_widths):
			c.setFont("Helvetica-Bold", 10)
			c.setFillColor(colors.black)
			c.drawCentredString((wReal/2)+20,hReal, "*** LIBRO DE INVENTARIO Y BALANCE - CUENTA 49 - PASIVO DIFERIDO DEL MES DE %s ***"%(self.period.name))
			c.setFont("Helvetica-Bold", 10)
			c.drawString(30,hReal-10, particionar_text( self.company_id.name,90))
			c.setFont("Helvetica", 9)
			c.drawString(30,hReal-20,particionar_text( self.company_id.partner_id.street if self.company_id.partner_id.street else '',100))
			c.drawString(30,hReal-30, self.company_id.partner_id.state_id.name if self.company_id.partner_id.state_id else '')
			c.drawString(30,hReal-40, self.company_id.partner_id.vat if self.company_id.partner_id.vat else '')


			c.setFont("Helvetica", 10)
			style = getSampleStyleSheet()["Normal"]
			style.leading = 8
			style.alignment= 1

			data= [[Paragraph("<font size=8><b>INFORMACION DEL PROVEEDOR</b></font>",style),'','',
				Paragraph("<font size=8><b>TD</b></font>",style),
				Paragraph("<font size=8><b>NUMERO DEL DOCUMENTO</b></font>",style),
				Paragraph("<font size=8><b>F. DE EMISION DEL COMP.DE PAGO</b></font>",style),
				Paragraph("<font size=8><b>MONTO DE LA CUENTA POR COBRAR</b></font>",style)],
				[Paragraph("<font size=8><b>DOCUMENTO DE IDENTIDAD</b></font>",style),'',
				Paragraph("<font size=8><b>APELLIDOS Y NOMBRES DENOMINACION O RAZON SOCIAL</b></font>",style),
				'',''],
				[Paragraph("<font size=8><b>TIPO</b></font>",style),
				Paragraph("<font size=8><b>NUMERO</b></font>",style),
				'','','']]
			t=Table(data,colWidths=size_widths, rowHeights=[18,18,18])
			t.setStyle(TableStyle([
				('SPAN',(0,0),(2,0)),
				('SPAN',(0,1),(1,1)),
				('SPAN',(2,1),(2,2)),
				('SPAN',(3,0),(3,2)),
				('SPAN',(4,0),(4,2)),
				('SPAN',(5,0),(5,2)),
				('SPAN',(6,0),(6,2)),
				('GRID',(0,0),(-1,-1), 1.5, colors.black),
				('ALIGN',(0,0),(-1,-1),'CENTER'),
				('VALIGN',(0,0),(-1,-1),'MIDDLE'),
				('TEXTFONT', (0, 0), (-1, -1), 'Calibri'),
				('LEFTPADDING', (0,0), (-1,-1), 2),
				('RIGHTPADDING', (0,0), (-1,-1), 2),
				('BOTTOMPADDING', (0,0), (-1,-1), 2),
				('TOPPADDING', (0,0), (-1,-1), 2),
				('FONTSIZE',(0,0),(-1,-1),4)
			]))
			t.wrapOn(c,30,500) 
			t.drawOn(c,30,hReal-100)

		def verify_linea(self,c,wReal,hReal,posactual,valor,pagina,size_widths):
			if posactual <50:
				c.showPage()
				pdf_header(self,c,wReal,hReal,size_widths)
				return pagina+1,hReal-120
			else:
				return pagina,posactual-valor

		width ,height  = 842,595
		wReal = width- 15
		hReal = height - 40

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file
		name_file = "cta_49.pdf"
		c = canvas.Canvas( direccion + name_file, pagesize= (842,595) )
		pos_inicial = hReal-40
		pagina = 1

		size_widths = [50,100,250,50,130,90,100]

		pdf_header(self,c,wReal,hReal,size_widths)

		pos_inicial = pos_inicial-70

		c.setFont("Helvetica",9)
		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		self.env.cr.execute(_get_sql_vst_49(self))
		res = self.env.cr.dictfetchall()

		cont = 0
		doc_partner = ''
		saldo_mn, final_mn = 0, 0

		for i in res:
			first_pos = 30

			c.setFont("Helvetica-Bold", 9)
			if cont == 0:
				doc_partner = i['doc_partner']
				cont += 1
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			if doc_partner != i['doc_partner']:
				c.line(700,pos_inicial+3,795,pos_inicial+3)
				c.drawString( 575 ,pos_inicial-5,'TOTAL:')
				c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )

				saldo_mn = 0

				pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
				c.setFont("Helvetica-Bold", 9)

				doc_partner = i['doc_partner']
				c.drawString( first_pos+2 ,pos_inicial,'Cliente: ' + i['doc_partner'] if i['doc_partner'] else '')
				pos_inicial -= 15

			c.setFont("Helvetica", 8)
			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_partner'] if i['td_partner'] else '',50) )
			first_pos += size_widths[0]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['doc_partner'] if i['doc_partner'] else '',50) )
			first_pos += size_widths[1]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['partner'] if i['partner'] else '',230) )
			first_pos += size_widths[2]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['td_sunat'] if i['td_sunat'] else '',100) )
			first_pos += size_widths[3]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['nro_comprobante'] if i['nro_comprobante'] else '',100) )
			first_pos += size_widths[4]

			c.drawString( first_pos+2 ,pos_inicial,particionar_text( i['fecha_doc'] if i['fecha_doc'] else '',100) )
			first_pos += size_widths[6]

			c.drawRightString( first_pos+85 ,pos_inicial,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % i['saldo_mn'])) )
			saldo_mn += i['saldo_mn']
			final_mn += i['saldo_mn']

			pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)

		c.setFont("Helvetica-Bold",9)
		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-5,'TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % saldo_mn)) )
		pos_inicial -= 10

		pagina, pos_inicial = verify_linea(self,c,wReal,hReal,pos_inicial,12,pagina,size_widths)
		c.setFont("Helvetica-Bold", 9)

		c.line(700,pos_inicial+3,795,pos_inicial+3)
		c.drawString( 575 ,pos_inicial-10,'SALDO FINAL TOTAL:')
		c.drawRightString( 795,pos_inicial-10,'{:,.2f}'.format(decimal.Decimal ("%0.2f" % final_mn)) )

		c.save()

		f = open(str(direccion) + name_file, 'rb')		
		return self.env['popup.it'].get_file('LIBRO DE INVENTARIO Y BALANCE - DETALLE CUENTA 49 '+ self.period.name,base64.encodestring(b''.join(f.readlines())))