# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class UpdateAccountAnalyticWizard(models.TransientModel):
	_name = 'update.account.analytic.wizard'

	analytic_account_id = fields.Many2one('account.analytic.account',string=u'Cuenta Analítica')

	def edit_line_analytic_account_id(self):
		line_obj = self.env['account.move.line']
		line_obj.browse(self.env.context['active_ids']).with_context({'analytic_account_id':self.analytic_account_id.id,'active_ids':self.env.context['active_ids']}).update_account_analytic_account_line()
		return self.env['popup.it'].get_message(u'SE EDITARON CORRECTAMENTE LAS LINEAS CON LA CUENTA ANALITICA SELECCIONADA.')

	def edit_line_analytic_account_analytic_id(self):
		line_obj = self.env['account.analytic.line']
		line_obj.browse(self.env.context['active_ids']).with_context({'analytic_account_id':self.analytic_account_id.id,'active_ids':self.env.context['active_ids']}).update_account_analytic_account_line()
		return self.env['popup.it'].get_message(u'SE EDITARON CORRECTAMENTE LAS LINEAS CON LA CUENTA ANALITICA SELECCIONADA.')