# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	def update_type_number_it(self):
		type_document_id = self.env.context['type_document_id']
		type_document_obj = self.env['einvoice.catalog.01'].browse(type_document_id)
		nro_comp = self.env.context['nro_comp']
		for line in self:
			line.type_document_id = type_document_obj.id
			line.nro_comp = nro_comp

	def update_expected_date_it(self):
		expected_date = self.env.context['expected_date']
		for line in self:
			line.expected_pay_date = expected_date

	@api.model
	def action_update_type_number_it(self):
		wizard = self.env['account.mline.type.number.update.wizard'].create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_account_mline_type_number_update_wizard_form' % module)
		return {
			'name':u'Fusionar Comprobantes',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'account.mline.type.number.update.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

	@api.model
	def action_update_expected_date_it(self):
		wizard = self.env['account.mline.expected.date.update.wizard'].create({})
		module = __name__.split('addons.')[1].split('.')[0]
		view = self.env.ref('%s.view_account_mline_expected_date_update_wizard_form' % module)
		return {
			'name':u'Actualizar Fecha Prevista de Pago',
			'res_id':wizard.id,
			'view_mode': 'form',
			'res_model': 'account.mline.expected.date.update.wizard',
			'view_id': view.id,
			'context': self.env.context,
			'target': 'new',
			'type': 'ir.actions.act_window',
		}