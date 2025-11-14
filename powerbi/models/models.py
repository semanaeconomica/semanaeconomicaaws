from odoo import models, fields, api
from datetime import datetime
from datetime import date

from odoo.exceptions import ValidationError

class powerbi_reporte(models.Model):
    _inherit = 'sale.report'
    _description = 'Campos para power bi'

    name_partner = fields.Char(related="order_id.partner_id.name")
    name_sell = fields.Char(related="order_id.user_id.name")
    # f_ini_sol
    number_order = fields.Integer(related='order_id.purchase_order_count', string='Número de Pedido')
    name_product= fields.Char(related='product_id.name', string='Producto')
    # edicion
    date_edition = fields.Date(string='Fecha edición', compute='get_data')
    # product_uom_qty
    # price_subtotal
    plazo_pago = fields.Char(related='payment_term_id.name', string='Plazo de Pago') # sale.order.line
    categoria = fields.Char(related='categ_id.parent_id.name', string='Categoria')
    subcategoria = fields.Char(related='categ_id.name', string='Categoria')
    # f_ini_sus
    # f_fin_sus
    name_contract_type = fields.Char(related='order_id.suscriptions_ids.type_contract_id.display_name')
    # state
    id_odoo8 = fields.Integer(related='order_id.id_odoo8', string='')

    def get_data(self):
        for record in self:
            for order_line in record.order_id.order_line:
                if order_line.product_id == record.product_id and order_line.product_uom_qty == record.product_uom_qty and record.f_ini_sol == order_line.subscription_start_date:
                        record.date_edition = order_line.edition_id.date_start

            if record.date_edition == False:
                # record.date_edition = datetime.strptime('01-01-2000', '%m-%d-%Y').date()
                record.date_edition = ''
