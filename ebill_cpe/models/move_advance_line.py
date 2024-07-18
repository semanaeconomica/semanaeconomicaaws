from odoo import models, fields, api
from odoo.addons.payment.models.payment_acquirer import ValidationError

class MoveAdvanceLine(models.Model):
    _inherit = 'move.advance.line'
    account_line_move_id = fields.Many2one('account.move.line',string="Linea de Anticipo",
                                           required=True,domain="[('move_id', '=', move_id ),('is_anticipo','!=',False),('product_id','!=',False)]")
    anticipo_id = fields.Many2one('account.move', string="Factura Anticipo")
    account_line_move_id_name = fields.Char(compute="get_name_anticipo",string='Linea de Anticipo')
    @api.depends('account_line_move_id_name','serie','number')
    def get_name_anticipo(self):
        for record in self:
            product = str(record.account_line_move_id.product_id.name) if record.account_line_move_id and record.account_line_move_id.product_id else ''
            price_total = str(record.account_line_move_id.price_total) if record.account_line_move_id and record.account_line_move_id.price_total else ''

            if not product:
                record.account_line_move_id_name = 'no se encontro un anticipo en la factura'
            else:
                record.account_line_move_id_name = product+"/"+price_total

    _sql_constraints = [
        ('unique_anticipo_id', 'unique(anticipo_id,move_id)', 'ya se ingreso ese anticipo')
    ]


    @api.onchange('account_line_move_id')
    def change_move_line(self):
        for record in self:
            if record.account_line_move_id and not record.account_line_move_id.is_anticipo:
                raise ValidationError('solo puede seleccionar un anticipo')

    @api.onchange('serie','number')
    def change_serie_number(self):
        for record in self:

            inv = record.move_id.invoice_line_ids
            if inv and not record.account_line_move_id:

                for l in inv:
                    if l.product_id:

                        if l.product_id and l.is_anticipo and not l.move_advance_line_id:
                            record.account_line_move_id = l._origin.id



    @api.onchange('anticipo_id')
    def change_anticipo(self):

        for record in self:

            if not record.anticipo_id:
                return

            serie = record.anticipo_id.ref
            if not serie:
                raise ValidationError('el anticipo no tiene serie')
            series = serie.split('-')
            if (len(series)==2):
                record.serie = str(series[0])
                #raise ValidationError(int(series[1]))
                record.number = str(int(series[1]))
            else:
                raise ValidationError('formato de la serie incorrecto')

            inv = record.move_id.invoice_line_ids
            if inv:
                for l in inv:
                    if l.product_id:
                        if l.product_id and l.is_anticipo and not l.move_advance_line_id:
                            #raise ValidationError(l.id)
                            record.account_line_move_id = l._origin.id

