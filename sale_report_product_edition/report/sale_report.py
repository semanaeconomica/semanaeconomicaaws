# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):
    _inherit = 'sale.report'

    account_fiscal_year_id = fields.Many2one('account.fiscal.year',string="Periodo")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['account_fiscal_year_id'] = ', pei.fiscal_year_id as account_fiscal_year_id'

        groupby += ', pei.fiscal_year_id'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
