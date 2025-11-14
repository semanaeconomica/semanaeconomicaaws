# -*- coding: utf-8 -*-
from odoo import api, models, fields

import logging
log = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    billing_type = fields.Selection(selection_add=[('2', 'Conflux PSE')])

    def _l10n_pe_prepare_dte(self):
        res = super(AccountMove, self)._l10n_pe_prepare_dte()
        seq_split = self.ref.split('-')
        if len(seq_split)==2:
            dte_serial = seq_split[0]
            dte_number = seq_split[1]
        res['dte_serial'] = dte_serial
        res['dte_number'] = dte_number
        res['invoice_type_code'] = self.type_document_id.code
        res['currency_rate'] = self.currency_rate
        res['operation_type'] = self.op_type_sunat_id.code if self.op_type_sunat_id else '0101'
        if res['invoice_type_code']=='07' or res['invoice_type_code']=='08':
            #res['credit_note_type'] = self.doc_invoice_relac[0].
            if res['invoice_type_code']=='07':
                res['credit_note_type'] = self.credit_note_type_id.code
            if res['invoice_type_code']=='08':
                res['debit_note_type'] = self.debit_note_type_id.code
            res['rectification_ref_type'] = self.doc_invoice_relac[0].type_document_id.code
            res['rectification_ref_number'] = self.doc_invoice_relac[0].nro_comprobante
        if res['operation_type']=='1001':
            res["detraction"]=True
            res["detraction_amount"]=self.detraction_amount
            res["detraction_percent"]=self.detraction_type_id.percentage
            res["detraction_code"]=self.detraction_type_id.code
            res["detraction_payment_method_code"]=self.detraction_payment_id.code
        '''if res['perception_amount']>0:
            res['operation_type'] = '2001'''
        if self.guide_line_ids:
            res['remission_guides'] = []
            for guide in self.guide_line_ids:
                res['remission_guides'].append({
                    'type':'09',
                    'number': guide['numberg'],
                })
        '''if res['payment_term_is_credit']:
            res['payment_term_fees'] = document['payment_term_fees'].append({
                    "due_date": document['date_due'],
                    "amount": self.amount_total,
                    "code": "Cuota001"
                })'''
        return res

    def _l10n_pe_edi_get_extra_report_values(self):
        res = super(AccountMove, self)._l10n_pe_edi_get_extra_report_values()
        self.ensure_one()
        invoice_report_name = ''
        if self.type_document_id.code=='01':
            invoice_report_name = 'Factura Electronica'
        elif self.type_document_id.code=='03':
            invoice_report_name = 'Boleta Electronica'
        elif self.type_document_id.code=='07':
            invoice_report_name = 'Nota de credito Electronica'
        elif self.type_document_id.code=='08':
            invoice_report_name = 'Nota de debito Electronica'
        return {
            "invoice_report_name": invoice_report_name,
        }

    @api.onchange('credit_note_type_id')
    def _onchange_itgrupo_credit_note_type_id(self):
        if self.credit_note_type_id:
            self.l10n_pe_dte_credit_note_type = self.credit_note_type_id.code

    @api.onchange('debit_note_type_id')
    def _onchange_itgrupo_debit_note_type_id(self):
        if self.debit_note_type_id:
            self.l10n_pe_dte_debit_note_type = self.debit_note_type_id.code

    @api.onchange('op_type_sunat_id')
    def _onchange_itgrupo_op_type_sunat_id(self):
        if self.op_type_sunat_id:
            self.l10n_pe_dte_operation_type = self.op_type_sunat_id.code

    def l10n_pe_dte_credit_amount_single_fee(self):
        res = super(AccountMove, self).l10n_pe_dte_credit_amount_single_fee()
        if self.currency_id.name!='PEN':
            res+=-self.detraction_amount/self.currency_rate
        else:
            res+=-self.detraction_amount
        return res

    def _get_l10n_pe_dte_qrcode(self):
        res = super(AccountMove, self)._get_l10n_pe_dte_qrcode()
        if res != '':
            qr_string = ''
            dte_serial = ''
            dte_number = ''
            seq_split = self.ref.split('-')
            if len(seq_split)==2:
                dte_serial = seq_split[0]
                dte_number = seq_split[1]
            res = []
            res.append(self.company_id.vat or '')
            res.append(dte_serial)
            res.append(dte_number)
            res.append(str(round(0.0, 2)))
            res.append(str(round(self.l10n_pe_dte_amount_total, 2)))
            res.append(self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else '')
            res.append(self.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or '')
            res.append(self.partner_id.vat or '')
            qr_string = '|'.join(res)
            return qr_string
        else:
            return res