# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	@api.model
	def action_account_anticipos_wizard(self):
		wizard = self.env['account.anticipos.wizard'].create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_account_anticipos_wizard_form' % module)
		return {
			'name':u'Aplicar Anticipo',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'account.anticipos.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	def apply_anticipo_line(self):
		type_document_id = self.env.context['type_document_id']
		type_document_obj = self.env['einvoice.catalog.01'].browse(type_document_id)
		nro_comp = self.env.context['nro_comp']
		for move in self:
			for line in move.line_ids:
				if line.is_advance_check:
					line.type_document_id = type_document_obj.id
					line.nro_comp = nro_comp