# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api

class DeleteMoveXmlImport(models.Model):
	_name = 'delete.move.xml.import'

	name = fields.Char(string=u'Nombre')
	date = fields.Date(string=u'Fecha Importación')
	move_ids = fields.One2many('account.move', 'xml_import_code', string='Asientos')
	move_line_ids = fields.One2many('account.move.line', 'xml_import_code', string='Lineas')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones XML Facturas')], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones XML Facturas','implementation':'no_gap','active':True,'prefix':'IXML-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(DeleteMoveXmlImport,self).create(vals)
		return t

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)

	def open_line_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_account_moves_all').read()[0]
		domain = [('id', 'in', self.move_line_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_line_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)
