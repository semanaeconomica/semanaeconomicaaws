# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	def generar_wizard(self):
		wizard = self.env['sequence.wizard'].create({'name':'Generar Secuencia'})
		wizard.journal_id = self.id
		return {
			'res_id':wizard.id,
			'view_type':'form',
			'view_mode':'form',
			'res_model':'sequence.wizard',
			'views':[[self.env.ref('account_journal_sequence.sequence_wizard_view').id,'form']],
			'type':'ir.actions.act_window',
			'target':'new'
		}