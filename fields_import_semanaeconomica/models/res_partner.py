# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
	_inherit = 'res.partner'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)


class sale_order(models.Model):
	_inherit = 'sale.order'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)


class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)


class suscription_sale_order(models.Model):
	_inherit = 'suscription.sale.order'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)


class sync_se_sesi_etiquetas(models.Model):
	_inherit = 'sync.se.sesi.etiquetas'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)

class route_yaros(models.Model):
	_inherit = 'route.yaros'

	id_odoo8 = fields.Integer('ID Odoo8',copy=False)