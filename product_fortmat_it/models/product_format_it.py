# -*- coding: utf-8 -*-

from odoo import models, fields, api
class product_format_it(models.Model):
	_name = 'product.format.it'

	code = fields.Char(u'Código')
	name = fields.Char(u'Espacio')
	acron = fields.Char(u'Acrónimo')
	type_format_id = fields.Many2one('product.type.format.it',u'Tipo')
	percent = fields.Float(u'Porcentaje',digits=(6,2))
	formato = fields.Char(u'Formato')
	color_rot = fields.Char(u'Color Rótulo')
	color_text = fields.Char(u'Color Texto')
	sangria = fields.Boolean(u'Sangría',default=False)
	pub_inf = fields.Boolean(u'Publicidad Infantil',default=False)
	encarte = fields.Boolean(u'Encarte',default=False)
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)	

	# boolean_toggle

	

class product_type_format_it(models.Model):
	_name='product.type.format.it'

	name=fields.Char('Tipo')