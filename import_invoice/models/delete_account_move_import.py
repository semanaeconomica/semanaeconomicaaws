# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api

class DeleteAccountMoveImport(models.Model):
	_name = 'delete.account.move.import'

	name = fields.Char(string=u'Nombre')
	date = fields.Date(string=u'Fecha Importación')
	move_ids = fields.One2many('account.move', 'code_import_invoice', string='Facturas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	nro_entrega = fields.Char(string='N° de Entrega',readonly=True)
	nro_caja = fields.Char(string='N° de Caja',readonly=True)
	
	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones Facturas')], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones Facturas','implementation':'no_gap','active':True,'prefix':'IMF-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(DeleteAccountMoveImport,self).create(vals)
		return t

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)
