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



