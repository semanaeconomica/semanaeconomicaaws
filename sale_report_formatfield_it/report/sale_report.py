# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):
    _inherit = 'sale.report'

    format_id = fields.Many2one('product.format.it',string="Formato")

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['format_id'] = ', l.format_id as format_id'

        groupby += ', l.format_id'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
