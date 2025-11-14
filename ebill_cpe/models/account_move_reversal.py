from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'
    #guardar la factura que origina la nota de credito (factura rectificativa)
    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        res['move_refund_origin'] = move.id if move else False
        return res
