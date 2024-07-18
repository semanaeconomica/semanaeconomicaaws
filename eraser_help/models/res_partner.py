# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import expression

class ResPartner(models.Model):
	_inherit = 'res.partner'

	vat = fields.Char(string='Tax ID',help='')