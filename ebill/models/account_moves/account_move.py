# -*- coding: utf-8 -*-

from odoo import models, fields, api
from decimal import *
from odoo.exceptions import UserError
import json
from datetime import *
import urllib3
import re
import base64
import json

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.misc import formatLang, format_date

FACT_DATA_LABELS = ['Nro Documento Emisor : ', 'Tipo de Comprobante : ', 'Serie : ', 'Numero : ', 'IGV : ', 'Total : ',
                    'Fecha Emision : ',
                    'Tipo de Documento : ', 'Nro de Documento : ', 'Codigo Hash : ', '']


class AccountMove(models.Model):
    _inherit = 'account.move'
    op_type_sunat_id = fields.Many2one('einvoice.catalog.51', string='Tipo de Operacion SUNAT')
    debit_note_type_id = fields.Many2one('einvoice.catalog.10', string='Tipo de Nota de Debito')
    credit_note_type_id = fields.Many2one('einvoice.catalog.09', string='Tipo de Nota de Credito')
    related_code = fields.Char(related='type_document_id.code', store=True)
    hash_code = fields.Char(string='Codigo Hash', copy=False)
    print_version = fields.Char(string='Version Impresa', copy=False)
    xml_version = fields.Char(string='Version XML', copy=False)
    cdr_version = fields.Char(string='Version CDR', copy=False)
    qr_code = fields.Char(string='Codigo QR', copy=False)
    print_web_version = fields.Char(string='Version Impresa Web', copy=False)
    file_name = fields.Char(copy=False)
    binary_version = fields.Binary(string='Version Binaria', copy=False)
    billing_type = fields.Selection([('0', 'Nubefact'), ('1', 'Odoo Facturacion')], string='Tipo de Facturador')
    einvoice_id = fields.Many2one('einvoice', string='Facturacion Electronica', copy=False)
    advance_ids = fields.One2many('move.advance.line', 'move_id', copy=False)
    sunat_state = fields.Selection([('0', 'Esperando Envio'),
                                    ('1', 'Aceptada por SUNAT'),
                                    ('2', 'Rechazada'),
                                    ('3', 'Enviado')], string='Estado de Facturacion', default='0', copy=False, tracking=True)
    detraction_type_id = fields.Many2one('einvoice.catalog.54', string='Tipo de Detraccion')
    detraction_amount = fields.Float(string='Monto de Detraccion')
    retencion_amount = fields.Float(string='Monto de Retencion')
    detraction_payment_id = fields.Many2one('einvoice.catalog.payment', string='Medio de Pago Detraccion')
    codigo_unico = fields.Char(string='Codigo Unico CPE', copy=False)
    delete_reason = fields.Text(string='Razon de Baja', limit=100)
    sunat_ticket_number = fields.Char(string='Numero de Ticket SUNAT',tracking=True)
    guide_line_ids = fields.One2many('move.guide.line', 'move_id')
    json_sent = fields.Char(string='JSON enviado', copy=False)
    json_response = fields.Char(string='JSON respuesta', copy=False)
    json_response_consulta = fields.Char(string='JSON respuesta consulta', copy=False)


    @api.onchange('detraction_type_id', 'amount_total_signed')
    def _get_detraction_amount(self):
        for record in self:
            if record.detraction_type_id and record.amount_total_signed:
                record.detraction_amount = record.amount_total_signed * record.detraction_type_id.percentage * 0.01
                record.retencion_amount = record.amount_total * record.detraction_type_id.percentage * 0.01

    @api.model
    def create(self, vals):
        t = super(AccountMove, self).create(vals)
        if t.type in ['out_invoice', 'out_refund']:
            t.billing_type = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)],
                                                               limit=1).billing_type or None
            catalog = self.env['einvoice.catalog.51'].search([('code', '=', '0101')], limit=1)
            if not t.op_type_sunat_id and catalog:
                t.op_type_sunat_id = catalog.id
        return t


    def check_format_numberg(self, numberg):
        match = re.match(r'\b[A-Z]|[0-9]{4}-[0-9]{1,}\b', numberg, re.I)
        if not match:
            raise UserError(
                u'El formato del número de guía "' + numberg + '" es incorrecto, el formato debe ser similar a "0001-00001"')

        return numberg







