# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
	_inherit = 'account.move'

	def ver_destinos(self):

		sql = """
			CREATE OR REPLACE view account_des_move as (SELECT row_number() OVER () AS id, * from vst_destinos where am_id = %s)""" % (
				str(self.id)
			)

		self.env.cr.execute(sql)

		self.env.cr.execute("SELECT * FROM account_des_move")
		res = self.env.cr.dictfetchall()

		if len(res) <= 0:
			raise UserError("No hay ningun destino.")
		else:
			return {
			'name': 'Destinos',
			'type': 'ir.actions.act_window',
			'res_model': 'account.des.move',
			'view_mode': 'tree',
			'view_type': 'form',
			'target': 'new',
		}