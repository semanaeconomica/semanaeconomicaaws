# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
	_inherit = "account.move"

	xml_import_code = fields.Many2one('delete.move.xml.import',string='Codigo Importacion XML',ondelete="cascade",copy=False)


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	xml_import_code = fields.Many2one('delete.move.xml.import',string='Codigo Importacion XML',copy=False)

	def update_account_account_it(self):
		account_id = self.env.context['account_id']
		for item in self:
			self._cr.execute('''
				UPDATE ACCOUNT_MOVE_LINE SET ACCOUNT_ID = %s WHERE ID = %s
				''' % (str(account_id),str(item.id)))
		return self.env.context['active_ids']

	@api.model
	def action_update_account_id_it(self):
		wizard = self.env['change.account.account.wizard'].create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_change_account_account_wizard_form' % module)
		return {
			'name':u'Cambiar de Cuenta',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'change.account.account.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}