# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPickingType(models.Model):
	_inherit = 'stock.picking.type'

	serie_guia = fields.Many2one('ir.sequence', string=u'Serie de guía')