# -*- coding: utf-8 -*-

from odoo import models
import logging
log = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        self.ensure_one()
        if self.is_downpayment and res.get('l10n_pe_dte_advance_line', False):
            if len(self.invoice_lines)>0:
                invoice = self.invoice_lines.filtered(lambda i: i.move_id.state not in ('cancel'))
                code_invoice = invoice[0].move_id.type_document_id.code
                l10n_pe_dte_advance_type = ''
                if code_invoice=='01':
                    l10n_pe_dte_advance_type = '02'
                elif code_invoice=='03':
                    l10n_pe_dte_advance_type = '03'
                res['l10n_pe_dte_advance_type'] = l10n_pe_dte_advance_type
                if invoice[0].ref:
                    invoice_seq = invoice[0].ref.split('-')
                    if len(invoice_seq)==2:
                        res['l10n_pe_dte_advance_serial'] = invoice_seq[0]
                        res['l10n_pe_dte_advance_number'] = invoice_seq[1]
        log.info(res)
        return res