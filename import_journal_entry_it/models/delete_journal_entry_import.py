# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, exceptions, api

class DeleteJournalEntryImport(models.Model):
	_name = 'delete.journal.entry.import'

	name = fields.Char(string=u'Nombre')
	date = fields.Date(string=u'Fecha Importación')
	ref = fields.Char(string=u'Referencia de Importación')
	move_ids = fields.One2many('account.move', 'code_import', string='Asientos')
	company_id = fields.Many2one('res.company',string=u'Compañía',default=lambda self: self.env.company)
	

	@api.model
	def create(self,vals):
		id_seq = self.env['ir.sequence'].search([('name','=','Importaciones Asientos Contables')], limit=1)
		if not id_seq:
			if not id_seq:
				id_seq = self.env['ir.sequence'].create({'name':'Importaciones Asientos Contables','implementation':'no_gap','active':True,'prefix':'IMP-','padding':5,'number_increment':1,'number_next_actual' :1})

		vals['name'] = id_seq._next()
		t = super(DeleteJournalEntryImport,self).create(vals)
		return t

	def open_entries(self):
		self.ensure_one()
		action = self.env.ref('account.action_move_journal_line').read()[0]
		domain = [('id', 'in', self.move_ids.ids)]
		context = dict(self.env.context, default_invoice_id=self.id)
		views = [(self.env.ref('account.view_move_tree').id, 'tree'), (False, 'form'), (False, 'kanban')]
		return dict(action, domain=domain, context=context, views=views)
