# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCurrency(models.Model):
	_inherit = 'res.currency'

	pse_code = fields.Char(string='Codigo Facturador')