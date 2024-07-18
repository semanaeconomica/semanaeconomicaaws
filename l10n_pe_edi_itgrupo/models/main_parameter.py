# -*- coding: utf-8 -*-
from odoo import api, models, fields

import logging
log = logging.getLogger(__name__)

class MainParameter(models.Model):
    _inherit = "main.parameter"

    billing_type = fields.Selection(selection_add=[('2', 'Conflux PSE')])