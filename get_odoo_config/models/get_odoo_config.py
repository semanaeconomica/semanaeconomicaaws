# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import config
import json
class GetOdooConfig(models.TransientModel):
	_name = 'get.odoo.config'

	def get_conf(self):
		config_json = json.dumps(config.options,indent=4)
		return self.env['popup.it'].get_message(config_json)