# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	def _prepare_reconciliation_move_line(self, move, amount):
		aml_dict = super(AccountBankStatementLine,self)._prepare_reconciliation_move_line(move, amount)
		aml_dict['nro_comp'] = self.ref or ''
		date_currency = self.date if self.date else fields.Date.today()
		cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('company_id','=',self.company_id.id)],limit=1)
		aml_dict['tc'] = cu_rate.sale_type
		return aml_dict

	def _prepare_reconciliation_move(self, move_ref):
		data = super(AccountBankStatementLine,self)._prepare_reconciliation_move(move_ref)
		data['glosa'] = self.name
		date_currency = self.date if self.date else fields.Date.today()
		cu_rate = self.env['res.currency.rate'].search([('name','=',date_currency),('company_id','=',self.company_id.id)],limit=1)
		data['currency_rate'] = cu_rate.sale_type
		return data