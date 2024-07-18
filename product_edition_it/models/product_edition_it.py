# -*- coding: utf-8 -*-

from odoo import models, fields, api
class product_edition_it(models.Model):
	_name = 'product.edition.it'
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = "Ediciones"
	_rec_name = "edition_name"


	name = fields.Char(u'Edición')
	fiscal_year_id = fields.Many2one('account.fiscal.year','Periodo')
	week=fields.Char('Semana')
	edition_name = fields.Char(u'Nombre de Edición')
	title= fields.Many2one('edition.title.it',u'Título')
	type_edition = fields.Selection([('normal','Normal'),('especial','Especial'),],'Tipo') 
	product_category_id = fields.Many2one('product.category',u'Categoría')
	date_start = fields.Date('Fecha de Inicio')
	date_close = fields.Date('Fecha de Cierre')
	date_stop = fields.Date('Fecha Final')
	meta = fields.Integer('Meta')
	meta_optimist = fields.Integer('Meta Optimista')
	user_ids = fields.Many2many('res.users','edition_users_rel','edition_id','user_id','Responsables')
	line_ids = fields.One2many('product.edition.line.it','main_id','Directores y Metas')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)

	
	url_link = fields.Char('Enlace')
	state = fields.Selection([('draft','Borrador'),('open','Abierto'),('review','Revisado'),('close','Cerrado'),],'Estados',default="draft",track_visibility='always')
	def close_edition(self):
		self.state='close'

	def toopen(self):
		self.state='open'

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name', '=', u'Ediciones Perú Económico')],limit=1)
		if not id_seq:
			id_seq = self.env['ir.sequence'].create({'name': u'Ediciones Perú Económico', 'implementation': 'no_gap','active': True, 'prefix': 'Entrega -', 'padding': 4, 'number_increment': 1, 'number_next_actual': 1})
		cads= id_seq._next()
		vals['name'] = cads
		

		return super(product_edition_it,self).create(vals)

class edition_title_it(models.Model):
	_name='edition.title.it'

	name=fields.Char(u'Título')


class product_edition_line_it(models.Model):
	_name = 'product.edition.line.it'

	main_id= fields.Many2one('product.edition.it',u'Edición')
	user_id = fields.Many2one('res.users','Responsables')
	meta_optimist = fields.Integer('Meta Optimista')
	approval_date = fields.Date(u'Fecha Aprobación')
	approval_state = fields.Selection([('unrecord',u'Sin acción'),('approve','Aprobada'),('reject','Rechazada'),],u'Aprovación')

	def set_approval(self):
		self.approval_state='approve'

		aprobada = True
		for l in self.main_id.line_ids:
			if l.approval_state!='approve':
				aprobada=False

		if aprobada:
			self.main_id.write({'state':'review'})

	def set_reject(self):
		self.approval_state='reject'
		self.main_id.write({'state':'reject'})



