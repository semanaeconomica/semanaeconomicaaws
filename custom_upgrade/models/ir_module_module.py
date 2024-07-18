# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from collections import defaultdict
from decorator import decorator
from operator import attrgetter
import importlib
import io
import logging
import os
import pkg_resources
import shutil
import tempfile
import zipfile

import requests

from docutils import nodes
from docutils.core import publish_string
from docutils.transforms import Transform, writer_aux
from docutils.writers.html4css1 import Writer
import lxml.html
import psycopg2

import odoo
from odoo import api, fields, models, modules, tools, _
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
from odoo.exceptions import AccessDenied, UserError
from odoo.osv import expression
from odoo.tools.parse_version import parse_version
from odoo.tools.misc import topological_sort
from odoo.http import request

_logger = logging.getLogger(__name__)

def assert_log_admin_access(method):
	"""Decorator checking that the calling user is an administrator, and logging the call.

	Raises an AccessDenied error if the user does not have administrator privileges, according
	to `user._is_admin()`.
	"""
	def check_and_log(method, self, *args, **kwargs):
		user = self.env.user
		origin = request.httprequest.remote_addr if request else 'n/a'
		log_data = (method.__name__, self.sudo().mapped('name'), user.login, user.id, origin)
		if not self.env.is_admin():
			_logger.warning('DENY access to module.%s on %s to user %s ID #%s via %s', *log_data)
			raise AccessDenied()
		_logger.info('ALLOW access to module.%s on %s to user %s #%s via %s', *log_data)
		return method(self, *args, **kwargs)
	return decorator(check_and_log, method)

class Module(models.Model):
	_inherit = 'ir.module.module'

	@assert_log_admin_access
	def multiple_button_immediate_upgrade(self):
		for i in self.ids:
			module = self.env['ir.module.module'].browse(i)
			module._button_immediate_function(type(module).button_upgrade)
		return self.env['popup.it'].get_message('Se actualizaron todos los modulos de manera correcta')