# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from openerp.models import BaseModel


class ir_attachment(models.Model):
	_inherit = 'ir.attachment'

	eliminar_automatico = fields.Boolean('Eliminar',default=False)

	@api.model
	def _eliminar_automatico(self):
		self.env['ir.attachment'].search([('eliminar_automatico','=',True)]).unlink()

	def get_download_ls(self):
		base_url = self.env['ir.config_parameter'].get_param('web.base.url')
		download_url = '/web/content/' + str(self.id) + '?download=true'
		return {
			"type": "ir.actions.act_url",
			"url": str(download_url),
			"target": "new",
		}

