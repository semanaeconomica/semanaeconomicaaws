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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    move_type = fields.Selection(related='move_id.type', store=True)
    einvoice_line_id = fields.Many2one('einvoice.line', copy=False)
    move_advance_line_id = fields.One2many('move.advance.line', 'account_line_move_id')
    is_anticipo = fields.Boolean(compute="get_is_anticipo", default=False, stored=True)
    is_free = fields.Boolean(compute="get_is_free", default=False, stored=True)
    is_discount = fields.Boolean(compute="get_is_discount", default=False, stored=True)

    price_subtotal_origin = fields.Float(string='Subtotal', store=True,digits=(12,10))
    price_total_origin = fields.Float(string='Total', store=True,digits=(12,10))
    billing_type = fields.Selection(related="move_id.billing_type")

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids')
    def _onchange_price_subtotal_origin(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal_origin())
            #raise ValidationError(line.price_subtotal_origin)
            #line.update(line._get_fields_onchange_subtotal_origin())

    def _get_price_total_and_subtotal_origin(self, price_unit=None, quantity=None, discount=None, currency=None, product=None,
                                      partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model_origin(
            price_unit=price_unit or self.price_unit,
            quantity=quantity or self.quantity,
            discount=discount or self.discount,
            currency=currency or self.currency_id,
            product=product or self.product_id,
            partner=partner or self.partner_id,
            taxes=taxes or self.tax_ids,
            move_type=move_type or self.move_id.type,
        )

    @api.model
    def _get_price_total_and_subtotal_model_origin(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_discount = price_unit * (1 - (discount / 100))
        subtotal = quantity * price_unit_discount


        # Compute 'price_total'.

        if taxes:
            taxes_res = taxes._origin.compute_all_origin(price_unit_discount,
                                                  quantity=quantity, currency=currency, product=product,
                                                  partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            #raise ValidationError('hi' + str(taxes_res))
            res['price_subtotal_origin'] = taxes_res['total_excluded']
            res['price_total_origin'] = taxes_res['total_included']
        else:
            res['price_total_origin'] = res['price_subtotal_origin'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        #if currency:
        #    res = {k: currency.round(v) for k, v in res.items()}
        #raise ValidationError(str(res))
        return res


    #function to  check if is an advance
    @api.depends('product_id','tax_ids')
    def get_is_free(self):
        for record in self:
            #free_transer_tax_ids = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
            #                                                         limit=1).free_transer_tax_ids
            free = ['2', '3', '4', '5', '6', '7', '10', '11', '12', '13', '14', '15']
            igv_type = None
            is_free = False
            for t in record.tax_ids:
                igv_type = t.eb_afect_igv_id.pse_code
                if igv_type in free:
                    is_free = True
                # or free_transer_tax_ids.invoice_repartition_line_ids.
            #if record.tax_repartition_line_id.tax_id.id in free_transer_tax_ids.ids:
            if record.tax_repartition_line_id.tax_id.eb_afect_igv_id.pse_code in free:
                is_free = True

            #for tg in record.tag_ids:



            record.is_free = is_free

    @api.depends('product_id')
    def get_is_anticipo(self):
        for record in self:
            is_anticipo = False
            parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)

            anticipos = parameters.advance_product_ids
            anticipos_ids = []
            for a in anticipos:
                anticipos_ids.append(a.product_id.id)
            if anticipos_ids and record.product_id:
                if record.product_id.id in anticipos_ids:
                    is_anticipo = True
            record.is_anticipo = is_anticipo

    @api.depends('product_id')
    def get_is_discount(self):
        for record in self:
            is_discount = False
            parameters = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            discounts = parameters.discounts_products_ids
            discounts_ids = []
            for d in discounts:
                discounts_ids.append(d.id)
            if discounts_ids and record.product_id:
                if record.product_id.id in discounts_ids:
                    is_discount = True
            record.is_discount = is_discount

    #action to return the view of einvoice line
    def get_einvoice_line(self):
        if self.einvoice_line_id:
            return {
                'res_id': self.einvoice_line_id.id,
                'view_mode': 'form',
                'res_model': 'einvoice.line',
                'views': [[self.env.ref('ebill.view_einvoice_line_form').id, 'form']],
                'type': 'ir.actions.act_window',
                'target': 'new'
            }



