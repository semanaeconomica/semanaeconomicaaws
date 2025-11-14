# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression


class account_payment(models.Model):
	_inherit = 'account.payment'

	destination_account_id = fields.Many2one('account.account', compute=False,store=True, readonly=True)

	@api.onchange('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
	@api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
	def _compute_destination_account_id_new(self):
		self._compute_destination_account_id()