# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ChangeAccountAccountWizard(models.TransientModel):
	_name = 'change.account.account.wizard'

	account_id = fields.Many2one('account.account',string='Cuenta')

	def update_account(self):
		line_obj = self.env['account.move.line']

		ids2 = line_obj.browse(self.env.context['active_ids']).with_context({'account_id':self.account_id.id,'active_ids':self.env.context['active_ids']}).update_account_account_it()
		ids2 = self.env.context['active_ids']
		if ids2==[]:
			raise UserError('No se actualizaron Cuentas, verifique sus datos')

		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CON EXITO LAS CUENTAS')