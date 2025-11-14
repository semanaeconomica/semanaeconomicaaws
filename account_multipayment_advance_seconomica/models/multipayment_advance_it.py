# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.osv import osv

class MultipaymentAdvanceIt(models.Model):
	_inherit = 'multipayment.advance.it'

	operation_type = fields.Char(string='T. Operacion',size=2)
	good_services = fields.Char(string='Bien o Servicio',size=3)

	def crear_asiento(self):
		t = super(MultipaymentAdvanceIt, self).crear_asiento()
		self.asiento_id.type_op_det = self.operation_type
		self.asiento_id.code_operation = self.good_services
		return t