from odoo import fields, models , api
from odoo.exceptions import UserError
from collections import defaultdict
from datetime import datetime


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ref_sale = fields.Many2one('sale.order','Referencia del pedido',compute='get_sale_origin')

    fecha_pedido = fields.Datetime(related='ref_sale.date_order')
    create_invoice_date = fields.Datetime(related='move_id.create_date', string='Fecha Creacion Factura')
    date_aprox_payment = fields.Date(related='move_id.date_aprox_payment', string='Fecha Pago')
    diff_1 = fields.Integer(compute='get_diff_1',string="F. Creacion Factura  - F. Pedido")
    diff_2 = fields.Integer(compute='get_diff_1', string="Fecha Pago  - F. Creacion Factura ")


    def action_show_details_sale(self):
        return {
            'name': self,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order',
            #'views': [(view.id, 'form')],
            #'view_id': view.id,
            'target': 'current',
            'res_id': self.ref_sale.id,
            'context': dict(
                self.env.context,
            ),
        }


    def get_diff_1(self):
        for record in self:
            record.diff_1 = (record.create_invoice_date - record.fecha_pedido).days
            #my_time = datetime.min.time()
            if record.date_aprox_payment:
                record.diff_2 = (record.date_aprox_payment - record.create_invoice_date.date()).days
            else:
                record.diff_2 = False


    ref_invoice = fields.Char(related='move_id.ref',string='Número de Factura')


    invoice_partner_id = fields.Many2one('res.partner',related='move_id.partner_id',string='Cliente')
    invoice_user_id = fields.Many2one('res.users', related='move_id.invoice_user_id', string='Vendedor')
    invoice_state = fields.Selection(related='move_id.state', string='Estado')

    @api.depends('sale_line_ids')
    def get_sale_origin(self):
        for record in self:
            sale_origin = False
            for sl in record.sale_line_ids:
                sale_origin = sl.order_id.id
            record.ref_sale = sale_origin

