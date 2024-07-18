from odoo import models, fields, api
BILLING_TYPE = [('0','Nubefact'),('1','Odoo Facturacion')]
from odoo.exceptions import UserError

class EbillParameter(models.Model):
    _name = 'ebill.parameter'
    _description = "holas"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    company_id = fields.Many2one('res.company', required=True , string="Compañia",default=lambda self: self.env.company,readonly=True)

    rounded_ebill_line = fields.Integer(default=10)
    rounded_ebill = fields.Integer(default=10)
    rounded_show_invoice = fields.Integer(default=2, string="Redondear en Factura")
    send_multi_credits = fields.Boolean(default=True)
    verify_amount_odoo = fields.Boolean(default=True,required=True)
    send_address = fields.Selection([('street', 'calle'),
                                     ('address_complete', 'Direccion Completa'),
                                     ('adress_complete_ubigeo', 'Direccion Completa Ubigeo')], required=True,
                                    default='address_complete')
    margen_error = fields.Float(default=0.04,digits=(12,10))
    set_amount_total = fields.Selection([('force','Establecer a Odoo'),
                                         ('force_cal','Establecer y calcular a Odoo')],default='force',
                                        string="Establecer Monto Total")
    detraccion_in_observaciones = fields.Boolean(string="Detraccion en Observaciones",default=True)
    retencion_equal_detraccion = fields.Boolean(string="Establecer Retencion igual a detraccion",default=True)
    validate_anticipo_amount  = fields.Boolean(string="Validar Monto de Anticipos",default=True)
    send_product_default_code = fields.Boolean(string='Enviar Codigo del Producto',default=True)
    send_customer_email = fields.Boolean(string='Enviar Correo Cliente',default=True)
    required_onu = fields.Boolean(string='ONU Obligatorio', default=True)
    use_isc = fields.Boolean(string='Usar ISC', default=False)
    modify_einvoice = fields.Boolean(string="Modificar Einvoice")


    #use_cal_line_odoo = fields.Boolean(default=True,string="Enviar Calculos Redondeados de Odoo a Nubefact")
    _sql_constraints = [
     ('unique_company', 'unique(company_id)', 'No puede haber dos Compañias iguales')
    ]

    def change_token_test(self):
        token = 'eyJhbGciOiJIUzI1NiJ9.ImU1MTdiNTJjNDRjMzQzZjg5OGU5Y2VjNWI2NWMxNzhiMTMzNjM3ZjMxYmU2NDZlMmEyYzFiNjY0MWQ5NmNmMzEi.7hJD1v2NusE0RPrcQqvw52Ei0w8v0yy2km8wkkfL72k'
        url = 'https://www.pse.pe/api/v1/7f7a9e4d7d0b494eb96c58bf732f97f157bd83ed86ab471aba9d00a8133e4eb4'
        sql = f"UPDATE serial_nubefact_line SET nubefact_token = '{token}' , nubefact_path = '{url}'"
        self.env.cr.execute(sql)

    def action_view_main_parameter(self):
        self.ensure_one()
        parameters = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)], limit=1)
        if not parameters:
            raise UserError('no existe parametro principal')

        return {
            'name': ('Parametro principal'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'main.parameter',
            #'views': [(view.id, 'form')],
            #'view_id': view.id,
            'target': 'current',
            'res_id': parameters.id,
            'context': dict(
                parameters.env.context,
            ),
        }

