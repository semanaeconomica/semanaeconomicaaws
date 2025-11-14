# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        if res.get('res_id', False):
            refund = self.env['account.move'].browse(res.get('res_id'))
            if refund:
                refund.write({
                    'l10n_pe_dte_credit_note_type': self.l10n_pe_dte_credit_note_type or '01',
                    'credit_note_type_id': self.env['einvoice.catalog.09'].search([('code','=', self.l10n_pe_dte_credit_note_type or '01')])[0].id
                    })
        return res