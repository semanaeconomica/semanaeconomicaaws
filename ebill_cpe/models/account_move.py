from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.payment.models.payment_acquirer import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'
    json_sent = fields.Char(string='JSON enviado', copy=False)
    json_response = fields.Char(string='JSON respuesta', copy=False)
    json_response_consulta = fields.Char(string='JSON respuesta consulta', copy=False)
    total_voucher = fields.Float(related="einvoice_id.total_voucher")
    total_voucher_rounded = fields.Float(related="einvoice_id.total_voucher_rounded")

    retencion_amount = fields.Float(string='Monto de Retencion')
    move_refund_origin = fields.Many2one('account.move',string="Factura Origen")

    is_note_credit_13 = fields.Boolean(compute='get_is_note_credit_13')

    amount_total_without_free = fields.Monetary(string='Total',
                                                readonly=True,compute='_compute_amount_without_free')

    amount_total_signed_without_free = fields.Monetary(string='Total',
                                                       readonly=True,compute='_compute_amount_without_free')
    msg_credit = fields.Char(compute="get_msg_credit",string="-")

    def set_anticipos_clear(self):
        for record in self:
            record.advance_ids.unlink()


    def set_anticipos(self):
        for record in self:
            record.advance_ids.unlink()
            for l in record.invoice_line_ids:
                l.get_is_anticipo()
                if not l.is_anticipo or l.is_anticipo == False:
                    continue
                #raise ValueError(l)
                record.advance_ids += self.env['move.advance.line'].new({
                    'move_id': record.id ,
                    'account_line_move_id': l.id
                })
                #raise ValueError(a)
                #l.get_name_anticipo()


    @api.depends('invoice_payment_term_id','invoice_date_due')
    def get_msg_credit(self):
        for record in self:
            total_dias = 0

            if  record.invoice_payment_term_id:
                plazos = record.invoice_payment_term_id.line_ids
                for p in plazos:
                    total_dias += p.days
            else:
                if self.invoice_date_due:
                    if self.is_note_credit_13:
                        if  self.move_refund_origin.invoice_date:
                            if self.invoice_date_due > self.move_refund_origin.invoice_date:
                                diff_fechas = self.invoice_date_due - self.move_refund_origin.invoice_date
                                total_dias = diff_fechas.days



                    else:
                        if self.invoice_date:
                            if self.invoice_date_due > self.invoice_date:
                                diff_fechas = self.invoice_date_due - self.invoice_date
                                total_dias = diff_fechas.days

            msg = ''
            if total_dias > 0 :
                msg = ' CREDITO'
            else:
                msg = ' AL CONTADO'
            record.msg_credit = msg

    def get_is_note_credit_13(self):
        for record in self:
            is_note_credit_13 = False
            if self.credit_note_type_id:
                if self.credit_note_type_id.code == '13':
                    is_note_credit_13 = True
            record.is_note_credit_13 = is_note_credit_13

    @api.onchange('credit_note_type_id')
    def change_dates_origin_refund(self):
        for record in self:
            if record.credit_note_type_id and record.move_refund_origin:
                record.get_is_note_credit_13()
                if record.is_note_credit_13 or record.is_note_credit_13 == True:
                    #record.invoice_date = record.move_refund_origin.invoice_date
                    record.invoice_payment_term_id = record.move_refund_origin.invoice_payment_term_id
                    #record.invoice_date_due = record.move_refund_origin.invoice_date_due


    def anulate_items(self):
        if not self.credit_note_type_id.code == '13':
            return
        array_products = []
        # raise ValueError(self.invoice_line_ids)
        # ValueError(self.invoice_line_ids)
        for l in self.invoice_line_ids:

            dx = {}
            if l.product_id:
                dx['product_id'] = l.product_id.id
            else:
                dx['name'] = l.name
            dx['price_unit'] = 0
            dx['account_id'] = l.account_id.id

            array_products.append(dx)

        # raise ValueError(array_products)
        # record.state == 'draft'
        self.button_draft()
        self.line_ids.unlink()

        for a in array_products:
            self.invoice_line_ids += self.env['account.move.line'].new(a)
        # raise ValueError(self.invoice_line_ids)

        self.action_post()


    def anulate_items_credit_13(self):
        for record in self:
            if record.credit_note_type_id and record.move_refund_origin:
                record.get_is_note_credit_13()
                if record.is_note_credit_13 or record.is_note_credit_13 == True:
                    if self.credit_note_type_id.code == '13':
                        record.anulate_items()



    @api.onchange('detraction_type_id', 'amount_total_signed')
    def _get_detraction_amount(self):
        parameter_ebill = self.company_id.parameter_ebill
        if not parameter_ebill:
            parameter_ebill = self.env['ebill.parameter'].create({
                'company_id': self.company_id.id
            })
        if not parameter_ebill:
            raise ValidationError('NO TIENE CONFIGURADO PARAMETROS CPE')


        for record in self:
            if record.detraction_type_id and record.amount_total_signed_without_free:
                #record.retencion_amount = record.amount_total_without_free * record.detraction_type_id.percentage * 0.01
                record.detraction_amount = record.amount_total_signed_without_free * record.detraction_type_id.percentage * 0.01

                # if record.detraction_amount:
                # condicion que hace que la reyencion sea igual a la detraccion (en la misma moneda que el total)
                if parameter_ebill.retencion_equal_detraccion and record.detraction_amount:
                    record.retencion_amount = record.amount_total_without_free * record.detraction_type_id.percentage * 0.01

                #raise ValueError(record.retencion_amount)
            else:
                record.detraction_amount = False
                record.retencion_amount = False

    #agregar las detracciones en observaciones
    @api.onchange('detraction_amount','detraction_type_id','retencion_amount')
    def add_detraccion_observaciones(self):
        txt_monto = 'Monto Detraccion: '
        txt_neto = 'Neto sin Detraccion : '
        for record in self:
            parameter_ebill = self.env.company.parameter_ebill

            obs = record.narration if record.narration else ''
            # eliminar los montos y netos
            spt = obs.split('\n')
            obs = ''
            for s in spt:
                if s.find(txt_monto) == -1 and s.find(txt_neto) == -1:
                    obs += s + '\n'

            record.narration = ''
            narration = ''


            if parameter_ebill.detraccion_in_observaciones:
                if record.retencion_amount and record.detraction_amount:
                    narration = txt_monto + str(round(record.retencion_amount, 2)) + "\n"
                    narration += txt_neto + str(round(record.amount_total - record.retencion_amount, 2)) + "\n"

            record.narration = narration + obs

    @api.depends(
        'line_ids.product_id',
        'line_ids.tax_ids',
        'line_ids.quantity',
        'line_ids.price_unit',
        'line_ids.debit',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount_without_free(self):
        #invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                try:
                    if line.is_free:
                        continue
                except:
                    if line._origin.is_free:
                        continue


                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            #move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            #move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total_without_free = sign * (total_currency if len(currencies) == 1 else total)
            #move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            #move.amount_untaxed_signed = -total_untaxed
            #move.amount_tax_signed = -total_tax
            move.amount_total_signed_without_free = abs(total) if move.type == 'entry' else -total
            #move.amount_residual_signed = total_residual

            #currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            #is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual

            # Compute 'invoice_payment_state'.
            '''
            if move.type == 'entry':
                move.invoice_payment_state = False
            elif move.state == 'posted' and is_paid:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'
            '''


