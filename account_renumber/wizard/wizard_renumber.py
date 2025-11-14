# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import *

class WizardRenumber(models.TransientModel):
	_name = "wizard.renumber"

	def get_period(self):
		fiscal_year = self.env['main.parameter'].search([('company_id','=',self.env.company.id)],limit=1).fiscal_year
		if not fiscal_year:
			raise UserError(u'No se ha configurado un Año Fiscal en parametros generales de Contabilidad de su Compañia')
		else:
			today = date.today()
			period = self.env['account.period'].search([('fiscal_year_id', '=', fiscal_year.id),
											   ('date_start', '<=', today),
											   ('date_end', '>=', today)],limit=1)
			if not period:
				raise UserError('No se encontro Periodo para la Fecha Actual')
			else:
				return period

	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company,readonly=True)
	period_id = fields.Many2one('account.period',string='Periodo',default=lambda self:self.get_period().id)
	first_number = fields.Integer(string=u'Primer Número',default=1)
	journal_ids = fields.Many2many('account.journal','account_renumber_journal_rel','id_wizard_renumber','id_journal_wizard',string=u'Libros', required=True)

	@api.onchange('period_id')
	def onchange_fiscal_year(self):
		return {'domain':{'period_id':[('fiscal_year_id','=',self.get_period().fiscal_year_id.id)]}}

	def renumber(self):
		if len(self.journal_ids)<1:
			raise UserError("Debe seleccionar al menos un libro")

		order_by = 'INVOICE_DATE,DATE'

		for journal in self.journal_ids:
			if journal.type == 'sale':
				order_by = 'TYPE, REF'
			sql = """UPDATE ACCOUNT_MOVE SET NAME = T.RNUM FROM
				(
				SELECT JOURNAL_ID, NAME, ID,INVOICE_DATE,DATE,
				'%s'||'-'||LPAD(((ROW_NUMBER() OVER (PARTITION BY JOURNAL_ID ORDER BY %s)::TEXT)::INTEGER+%s)::TEXT, 6, '0') AS RNUM
				FROM ACCOUNT_MOVE
				WHERE JOURNAL_ID = %s AND (DATE  BETWEEN '%s' AND '%s') AND IS_OPENING_CLOSE = FALSE AND STATE = 'posted' AND COMPANY_ID = %s
				ORDER BY JOURNAL_ID)T
				WHERE ACCOUNT_MOVE.ID =T.ID""" % (self.period_id.code[4:],order_by,str(self.first_number-1),str(journal.id),self.period_id.date_start.strftime('%Y/%m/%d'),self.period_id.date_end.strftime('%Y/%m/%d'),str(self.company_id.id))

			self.env.cr.execute(sql)
		return self.env['popup.it'].get_message('SE GENERO EXITOSAMENTE')