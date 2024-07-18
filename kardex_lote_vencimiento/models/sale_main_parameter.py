# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class stock_production_lot(models.Model):
	_inherit = 'stock.production.lot'

	vencimiento = fields.Date('Fecha Vencimiento')

