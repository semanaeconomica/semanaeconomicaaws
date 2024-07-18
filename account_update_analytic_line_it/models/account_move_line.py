# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	@api.model
	def action_update_account_analytic_wizard(self):
		wizard = self.env['update.account.analytic.wizard'].create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_update_account_analytic_wizard_form' % module)
		return {
			'name':u'Actualizar Cuenta Analítica',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'update.account.analytic.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def update_account_analytic_account_line(self):
		analytic_account_id = self.env.context['analytic_account_id']
		for line in self:
			line.analytic_account_id = analytic_account_id