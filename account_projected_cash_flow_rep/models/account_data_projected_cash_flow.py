# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountDataProjectedCashFlow(models.Model):
	_name = 'account.data.projected.cash.flow'

	name = fields.Char(default='Configuracion de Reporte de Flujo de Caja')
	account_id = fields.Many2one('account.account',string='Cuenta')
	is_draft = fields.Boolean(string='Considerar Borrador',default=False)
	date_due_option = fields.Selection([('1',u'Fecha de Cancelación'),('2',u'Fecha Vencimiento')],default='1',string='Fecha Ven')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)

	_sql_constraints = [
		('company_account_uniq', 'unique(account_id, company_id)',
		 u'Ya existe esta Cuenta configurada para Flujo de Caja Proyectado en esta Compañía'),
	]