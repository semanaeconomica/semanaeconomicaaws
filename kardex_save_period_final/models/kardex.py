# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class KardexSave(models.Model):
	_inherit = 'kardex.save'

