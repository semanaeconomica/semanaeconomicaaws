from odoo import fields, models

PRODUCT_SERVICE = [
    ('producto', 'Producto'),
    ('servicio', 'Servicio')
]
RESPONSE_TYPE = [
    ('carta', 'Carta domiciliaria'),
    ('email', 'E-mail')
]


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Identificacion del consumidor
    partner_address = fields.Char(string='Domicilio', required=True)
    partner_document_number = fields.Char(string='DNI/CE/RUC', required=True)
    partner_phone = fields.Char(string='Teléfono', required=True)

    # Identificacion del Bien contratado
    partner_product_service = fields.Selection(
        PRODUCT_SERVICE,
        string='Bien contratado',
        required=True
    )
    partner_amount = fields.Float(string='Monto del reclamo', required=True)

    # Detalles del reclamo
    partner_order = fields.Char(string='Pedido', required=True)

    # Tipo de respuesta
    partner_response_type = fields.Selection(
        RESPONSE_TYPE,
        string='Tipo de respuesta',
        required=True
    )

    # Observaciones
    response = fields.Text(string='Respuesta', required=True)
