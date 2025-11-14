# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class account_payment(models.Model):
    _inherit = "account.payment"

    #def _prepare_payment_moves(self):
    #    res = super(account_payment, self)._prepare_payment_moves()
    #    if self.is_personalized_change:
    #        for payment in res:
    #            list_moves = list(payment['line_ids'])
    #            for move in list_moves:
    #                list_lines = move[2]
    #                list_lines['credit'] = abs(list_lines['amount_currency']) / (1 / self.type_change) if list_lines['credit'] > 0 else  0
    #                list_lines['debit'] = list_lines['amount_currency'] / (1 / self.type_change) if list_lines['debit'] > 0 else  0
    #                list_lines['tc'] = self.type_change
    #    else:
    #        for payment in res:
    #            list_moves = list(payment['line_ids'])
    #            for move in list_moves:
    #                list_lines = move[2]
    #                list_lines['tc'] = self.currency_id._get_conversion_rate(self.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, self.payment_date or datetime.datetime.now())
    #    return res