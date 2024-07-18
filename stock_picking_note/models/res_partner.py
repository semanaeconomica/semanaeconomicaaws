# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = 'res.partner'

	number_driver_licence = fields.Char(string=u'Lic. de Conducir',size=20)