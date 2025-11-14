# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from odoo.osv import expression
import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_document_type_sequence(self):
        """ Return the match sequences for the given journal and invoice """
        self.ensure_one()
        if self.journal_id.l10n_latam_use_documents and self.l10n_latam_country_code == 'PE':
            res = self.journal_id.l10n_pe_sequence_ids.filtered(
                lambda x: x.l10n_latam_document_type_id == self.l10n_latam_document_type_id)
            return res
        return super()._get_document_type_sequence()

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if (self.journal_id.l10n_latam_use_documents and
                self.journal_id.company_id.country_id == self.env.ref('base.pe')):
            if self.journal_id.type == 'sale':
                document_type_ids = self.journal_id.l10n_pe_sequence_ids.mapped('l10n_latam_document_type_id').ids
            else:
                partner_domain = [
                    ('country_id.code', '=', 'PE'),
                    ('internal_type', 'in', ['invoice', 'debit_note', 'credit_note', 'invoice_in'])]
                if not self.partner_id:
                    pass
                elif self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                    partner_domain += [('code', 'in', ['01', '03', '07', '08', '09','00'])]
                elif self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                    partner_domain += [('code', 'in', ['03', '07', '08'])]
                document_type_ids = self.env['l10n_latam.document.type'].search(partner_domain).ids
            domain = expression.AND([domain, [('id', 'in', document_type_ids)]])
        return domain