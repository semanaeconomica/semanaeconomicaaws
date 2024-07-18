from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	invoice_payment_term_id_book = fields.Many2one(related='move_id.invoice_payment_term_id', readonly=True,store=True)