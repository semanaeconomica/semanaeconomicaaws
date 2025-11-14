# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalogPayment(models.Model):
	_inherit = 'einvoice.catalog.payment'

	pse_code = fields.Char(string='Codigo de Facturador', size=5)