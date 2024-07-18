from odoo import http
from odoo.http import request
import logging
import pprint
_logger = logging.getLogger(__name__)
from urllib.parse import urlparse
from odoo.addons.payment.models.payment_acquirer import ValidationError
from datetime import *
from odoo import models, fields, api

from urllib.parse import urlparse

class HookUpdateRate(http.Controller):
    @http.route(['/update_date_rate_js'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def index(self, **post):
        data = http.request.jsonrequest
        currency = http.request.env['res.currency'].sudo().env.ref('base.USD')
        http.request.env['res.currency'].sudo()._update_rates(data['date'],data['buy'],data['sale'],currency)