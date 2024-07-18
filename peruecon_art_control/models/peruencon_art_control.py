# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class sale_order_line(models.Model):
	_inherit='sale.order.line'

	date_recep = fields.Date(u'Fecha de Recepción')
	user_recep = fields.Many2one('res.users',u'Usuario Receptor')

	def sendemailart(self):
		config = self.env['peruecon.sale.config.it'].search([])
		if len(config)==0:
			return self.env['popup.it'].get_message(u'No se encuentra la configuración para envio de emails')

		if len(config[0].email_ids)==0:
			return self.env['popup.it'].get_message(u'No se configuraron correos electrónicos')

		for r in self:
			print(1)

			body_html = '%s <br/>'u'Num. Edición: %s | Producto: %s | Pedido de Venta: %s<br/>'% (config[0].text_email,r.edition_id.name, r.product_id.name,r.order_id.name)
			body_html +=  'Vendedor: %s | Cliente %s '%(r.salesman_id.name,r.order_partner_id.name)
			if r.date_recep==False:
				print(2)
				for k in config[0].email_ids:
					print(3)
					self.env['mail.mail'].create({
						'subject': 'Recordatorio de recepción de artes',
						'body_html': body_html,
						'email_to': k.email,
						}).send()
			if r.order_id.partner_id.email:
				self.env['mail.mail'].create({
					'subject': 'Recordatorio de recepción de artes',
					'body_html': body_html,
					'email_to': r.order_id.partner_id.email,
					}).send()

		return self.env['popup.it'].get_message(u'Se enviaron los correos electrónicos')

	def write(self, vals):
		if 'date_recep' in vals:
			vals['user_recep']=self.env.user.id
		return super(sale_order_line,self).write(vals)



class peruecon_sale_config_it(models.Model):
	_name='peruecon.sale.config.it'

	text_email = fields.Text(u'Mensaje para el Correo')
	email_ids = fields.One2many('peruecon.sale.config.email.it','main_id','Enviar a...')
	company_id = fields.Many2one('res.company',string=u'Compañía',required=True, default=lambda self: self.env.company)



class peruecon_sale_config_email_it(models.Model):
	_name='peruecon.sale.config.email.it'

	email = fields.Char(u'Correo Electrónico')
	main_id=fields.Many2one('peruecon.sale.config.it')