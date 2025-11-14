# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMlineExpectedDateUpdateWizard(models.TransientModel):
	_name = 'account.mline.expected.date.update.wizard'

	date = fields.Date(string='Fecha')

	def update_expected_date(self):
		line_obj = self.env['account.move.line']
		line_obj.browse(self.env.context['active_ids']).with_context({'expected_date':self.date,'active_ids':self.env.context['active_ids']}).update_expected_date_it()
		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CORRECTAMENTE LAS FECHAS PREVISTAS DE PAGO.')

	def update_expected_date_saldos(self):
		line_obj = self.env['account.balance.period.book']
		line_obj.browse(self.env.context['active_ids']).with_context({'expected_date':self.date,'active_ids':self.env.context['active_ids']}).update_expected_date_it()
		return self.env['popup.it'].get_message(u'SE ACTUALIZARON CORRECTAMENTE LAS FECHAS PREVISTAS DE PAGO.')