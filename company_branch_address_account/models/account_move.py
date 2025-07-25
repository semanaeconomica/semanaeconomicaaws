# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

import logging
log = logging.getLogger(__name__)


class AccountMove(models.Model):
	_inherit = 'account.move'

	company_branch_address_id = fields.Many2one('res.company.branch.address', 'Establecimiento Anexo', default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid) )

class AccountJournal(models.Model):
	_inherit = 'account.journal'

	company_branch_address_id = fields.Many2one('res.company.branch.address', 'Establecimiento Anexo', default=lambda self: self.env['res.users'].operating_unit_default_get(self._uid) )
