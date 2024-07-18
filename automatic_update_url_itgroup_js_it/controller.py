from odoo.addons.web.controllers.main import Home
from odoo.addons.web.controllers.main import Session

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


class Sessionx(Session):
    @http.route('/web/session/check', type='json', auth="user")
    def check(self):
        res = super(Sessionx, self).check()
        raise ValidationError('okaaa')
        #request.session.check_security()
        return res



