# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    code_sunat = fields.Char(string="Codigo Sunat",size=2)