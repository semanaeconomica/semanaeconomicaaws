# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog01(models.Model):
	_inherit = 'einvoice.catalog.01'

	pse_code = fields.Char(string='Codigo de Facturador')