# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class product_edition_it(models.Model):
	_inherit = 'product.edition.it'
	
	line_approv_ids = fields.One2many('product.edition.approval.it','main_id','Aprovaciones',copy=False)
	def toopen(self):
		super(product_edition_it,self).toopen()
		aprovs = self.env['edition.aprov.level.it'].search([('active','=',True)],order='order')
		a=[]
		for l in aprovs:
			print(l.user_id.id)

			h=self.env['product.edition.approval.it'].create({'user_id':l.user_id.id,'main_id':self.id})
			a.append(h)
		return a



class product_edition_approval_it(models.Model):
	_name='product.edition.approval.it'

	main_id=fields.Many2one('product.edition.it',u'Edición')
	user_id = fields.Many2one('res.users','Aprobador')
	approval_date = fields.Date(u'Fecha Aprobación')
	approval_state = fields.Selection([('approve','Aprobada'),('reject','Rechazada'),],u'Aprovación')
	order = fields.Integer('Orden')

	name = fields.Char(u'Edición',related='main_id.name')
	fiscal_year_id = fields.Many2one('account.fiscal.year','Periodo',related='main_id.fiscal_year_id')
	week=fields.Char('Semana')
	edition_name = fields.Char(u'Nombre de Edición',related='main_id.edition_name')
	title= fields.Many2one('edition.title.it',u'Título',related='main_id.title')
	date_start = fields.Date('Fecha de Inicio',related='main_id.date_start')
	date_close = fields.Date('Fecha de Cierre',related='main_id.date_close')
	url_link = fields	.Char('Enlace',related='main_id.url_link')
	company_id = fields.Many2one('res.company',string=u'Compañia',required=True, default=lambda self: self.env.company)
	state = fields.Selection('Estados',related='main_id.state')


	def set_approval(self):
		for r in self:
			if self.user_id.id != self.env.user.id:
				raise UserError(u'Solo el usuario asignado a esta línea de aprobación puede ejecutar esta acción')
			else:
				if r.main_id.state=='open':
					curr_order = r.order
					maxorder=0
					next_aprov=None
					config = r.env['ir.config_parameter']
					allap = 0
					prevaprov = True
					maxaprove = 0
					for n in r.main_id.line_approv_ids:
						if n.order==curr_order-1:
							if n.approval_state!='approve':
								prevaprov=False
						if n.order==curr_order+1:
							next_aprov = n
						if n.approval_state=='approve':
							allap=allap+1

					self.approval_state='approve'
					self.approval_date = fields.Date.today()
					if allap+1==len(r.main_id.line_approv_ids):
						self.main_id.write({'state':'review'})
						return self.env['popup.it'].get_message(u'Aprobaciones conpletas, APROBADO')


		

	def set_reject(self):
		for r in self:
			if self.user_id.id != self.env.user.id:
				raise UserError(u'Solo el usuario asignado a esta línea de aprobación puede ejecutar esta acción')
			if r.main_id.state=='open':
				if r.user_id.id != self.env.user.id:
					raise UserError(u'Solo el usuario asignado a esta línea de aprobación puede ejecutar esta acción')
				r.approval_state='reject'
				r.approval_date = None
				r.main_id.write({'state':'open'})
