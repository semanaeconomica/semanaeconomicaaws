# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
log = logging.getLogger(__name__)

class AccountDebitNote(models.TransientModel):
    _inherit = 'account.debit.note'

    def create_debit(self):
        res = super(AccountDebitNote, self).create_debit()
        if res.get('res_id', False):
            refund = self.env['account.move'].browse(res.get('res_id'))
            if refund:
                refund.write({
                    'debit_note_type_id': self.env['einvoice.catalog.10'].search([('code','=', self.l10n_pe_dte_debit_note_type or '01')])[0].id
                    })
        return res