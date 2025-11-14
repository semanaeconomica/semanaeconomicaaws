from odoo import models, fields, api

from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('invoice_line_ids')
    def update_taxes(self):
        for record in self:
            for r in record.invoice_line_ids:
                r._onchange_mark_recompute_taxes()
                r._onchange_price_subtotal()

                #r._onchange_mark_recompute_taxes_analytic()
                
                r._onchange_amount_currency()
                r._onchange_currency()
                r._compute_always_set_currency_id()
                r._amount_residual()
                r._compute_tax_line_id()
                r._compute_tax_audit()


            record._onchange_recompute_dynamic_lines()
            record._compute_amount()
            #record._inverse_amount_total()
            record._compute_payments_widget_reconciled_info()
            record._compute_invoice_taxes_by_group()
            record._compute_tax_lock_date_message()
            record._validate_move_modification()



