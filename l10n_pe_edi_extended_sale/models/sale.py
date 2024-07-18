# -*- coding: utf-8 -*-

from odoo import models

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        self.ensure_one()
        if self.is_downpayment:
            res['l10n_pe_dte_advance_line'] = True
            res['l10n_pe_dte_advance_amount'] = self.untaxed_amount_invoiced
            if len(self.invoice_lines)>0:
                invoice = self.invoice_lines.filtered(lambda i: i.move_id.state not in ('cancel'))
                res['l10n_pe_dte_advance_invoice_id'] = invoice[0].move_id.id
        return res