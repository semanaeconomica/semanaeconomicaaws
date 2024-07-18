from odoo import api, fields, models
from odoo.exceptions import UserError


class res_partner(models.Model):
	_inherit = "res.partner"

	receiver_contact = fields.Char('Contacto de Cobranza')
	responsible_followup_id = fields.Many2one('responsible.followup','Responsable de Seguimiento')
	date_next_action = fields.Date(u'Próxima Acción')
	text_next_action = fields.Text(u'Próxima Acción')
	partner_pay_promise = fields.Text(u'Promesa de Pago del Cliente')



class responsible_followup(models.Model):
	_name='responsible.followup'

	name=fields.Char('Responsable de Seguimiento')