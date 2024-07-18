# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from datetime import datetime, timedelta

class AccountProjectedCashFlowRep(models.TransientModel):
	_name = 'account.projected.cash.flow.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	date_end = fields.Date(string=u'Fecha Final',required=True,default=fields.Date.context_today)

	def get_report(self):
		self.env.cr.execute("""DELETE FROM account_projected_cash_flow_book WHERE user_id = %d"""%(self.env.uid))
	
		self.env.cr.execute("""
			INSERT INTO account_projected_cash_flow_book (grupo,concepto,account_id,fecha,amount,anio,mes,user_id) 
			("""+self._get_sql()+""")""")
		
		return {
				'name': 'Reporte de Flujo de Caja Proyectado',
				'type': 'ir.actions.act_window',
				'res_model': 'account.projected.cash.flow.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}


	def _get_sql(self):

		sql = """SELECT 
				CASE WHEN acf.grupo = '1' THEN '1-SALDO INICIAL'
				WHEN acf.grupo = '2' THEN '2-INGRESO'
				WHEN acf.grupo = '3' THEN '3-EGRESO'
				WHEN acf.grupo = '4' THEN '4-FINANCIAMIENTO' END AS grupo,
				acf.code||'-'||acf.item as concepto,
				a1.account_id,
				a1.fecha_ven as fecha,
				a1.saldo_mn as amount,
				CASE WHEN a1.fecha_ven IS NULL THEN 'INDEFINIDO'
				ELSE to_char(a1.fecha_ven::timestamp with time zone, 'yyyy'::text) END as anio,
				CASE WHEN a1.fecha_ven IS NULL THEN 'INDEFINIDO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '01' THEN '01-ENERO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '02' THEN '02-FEBRERO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '03' THEN '03-MARZO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '04' THEN '04-ABRIL'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '05' THEN '05-MAYO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '06' THEN '06-JUNIO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '07' THEN '07-JULIO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '08' THEN '08-AGOSTO'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '09' THEN '09-SEPTIEMBRE'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '10' THEN '10-OCTUBRE'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '11' THEN '11-NOVIEMBRE'
				WHEN to_char(a1.fecha_ven::timestamp with time zone, 'mm'::text) = '12' THEN '12-DICIEMBRE'
				ELSE '' END AS mes,
				%d AS user_id
				FROM get_saldos_projected_cash('%s','%s',%d) a1
				LEFT JOIN account_account a2 ON a2.id = a1.account_id
				LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
				LEFT JOIN account_cash_flow acf ON acf.id = a2.account_cash_flow_id
				WHERE a3.type in ('payable','receivable') and (a1.fecha_ven >= '%s' or a1.fecha_ven IS NULL)
				ORDER BY acf.grupo,acf.code
		""" % (self.env.uid,
			str(self.date_end.year) + '/01/01',
			self.date_end.strftime('%Y/%m/%d'),
			self.company_id.id,
			self.date_end.strftime('%Y/%m/%d'))
		
		return sql