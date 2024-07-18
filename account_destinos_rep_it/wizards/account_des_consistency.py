# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountDesConsistencyRep(models.TransientModel):
	_name = 'account.des.consistency.rep'

	name = fields.Char()
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	fiscal_year_id = fields.Many2one('account.fiscal.year',string=u'Ejercicio',required=True)
	period = fields.Many2one('account.period',string='Periodo',required=True)

	@api.onchange('company_id')
	def get_fiscal_year(self):
		if self.company_id:
			fiscal_year = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).fiscal_year
			if fiscal_year:
				self.fiscal_year_id = fiscal_year.id
			else:
				raise UserError(u'No existe un año Fiscal configurado en Parametros Principales de Contabilidad para esta Compañía')

	def get_report(self):

		sql = """
			CREATE OR REPLACE view account_des_consistency_book as (SELECT row_number() OVER () AS id , T.* FROM (%s)T)""" % (
				self.get_sql()
			)

		self.env.cr.execute(sql)

		return {
			'name': 'Consistencia Destinos',
			'type': 'ir.actions.act_window',
			'res_model': 'account.des.consistency.book',
			'view_mode': 'tree',
			'view_type': 'form',
		}

	def get_sql(self):
		sql = """
				select d1.periodo,d1.libro,d1.voucher,d1.cuenta,d1.debe,d1.haber
				from vst_diariog d1
				left join (
				select a1.move_id,a2.account_id,a2.debit,a2.credit,a4.a_debit,a4.a_credit from account_analytic_line a1
				left join account_move_line a2 on a2.id=a1.move_id
				left join account_account a3 on a3.id=a2.account_id
				left join account_analytic_account a4 on a4.id=a1.account_id
				where a3.check_moorage=TRUE) d2 on d2.move_id=d1.move_line_id

				left join
				(select aml.id, aml.account_id, aml.debit, aml.credit, aa.a_debit, aa.a_credit
				from account_move_line aml
				left join account_account aa on aa.id = aml.account_id
				where aa.check_moorage=TRUE) d3 on d3.id = d1.move_line_id
				left join account_account aa on aa.id = d1.account_id
				where d1.periodo = '%s' and d1.company_id = %s and aa.check_moorage = TRUE
				and (coalesce(d2.a_debit,0)+coalesce(d3.a_debit,0) = 0 or coalesce(d2.a_credit,0)+coalesce(d3.a_credit,0) = 0)
		""" % (str(self.period.code),str(self.company_id.id))
		return sql