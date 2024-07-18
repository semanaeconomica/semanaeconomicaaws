# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPlePurchaseBook(models.Model):
	_name = 'account.ple.purchase.book'
	_auto = False
	
	periodo = fields.Char(string='Periodo', size=50)
	fecha_cont = fields.Date(string='Fecha Cont.', size=15)
	libro = fields.Char(string='Libro', size=5)
	fecha_e = fields.Date(string='Fecha Em.', size=10)
	td = fields.Char(string='TD', size=64)
	serie = fields.Char(string=u'Serie')
	numero = fields.Char(string=u'Numero') 
	estado = fields.Char(string=u'Estado')
	estado_c = fields.Char(string=u'Estado Correcto')
	am_id = fields.Many2one(string=u'Factura')

	def view_account_move(self):

		return{

			'view_mode': 'form',
			'view_id': self.env.ref('account.view_move_form').id,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'res_id': self.am_id.id,
		}

	def action_fix_ple_purchase(self):
		for i in self:
			sql_update = """
				UPDATE account_move SET campo_41_purchase = '%s' WHERE id = %s """ % (
					i.estado_c, str(i.am_id.id)
				)

			self.env.cr.execute(sql_update)

		return self.env['popup.it'].get_message('SE ACTUALIZARON CORRECTAMENTE LOS CAMPOS PARA PLE.')