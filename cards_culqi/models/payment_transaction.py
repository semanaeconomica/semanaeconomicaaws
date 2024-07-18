# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class payment_transaction(models.Model):
    _inherit = 'payment.transaction'

    culqi_response = fields.Html( string="Culqi")
    id_culqi = fields.Char("Culqi Order ID")
    
    # Card Info
    culqi_response = fields.Html( string="Culqi")
    culqi_type = fields.Char("Tipo")
    culqi_card_brand = fields.Char("Marca de Tarjeta")
    culqi_card_type = fields.Char("Tipo de Tarjeta")
    culqi_card_number = fields.Char("Número")
    culqi_card_category = fields.Char("Categoria")

    # Issuer
    culqi_issuer_name =  fields.Char("Compañia emisora")

    culqi_outcome_merchant_type = fields.Char("Mensaje para el vendedor")
    culqi_outcome_merchant_message = fields.Char("Mensaje para el vendedor")

    