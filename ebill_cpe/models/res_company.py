from odoo import models, fields, api
from odoo.exceptions import UserError


class CompanyEbill(models.Model):
    _inherit = 'res.company'
    ebill_parameters = fields.One2many('ebill.parameter','company_id')
    parameter_ebill = fields.Many2one('ebill.parameter',compute="get_parameter_ebill")
    def get_parameter_ebill(self):
        for record in self:
            record.parameter_ebill = False
            if record.ebill_parameters:
                record.parameter_ebill = record.ebill_parameters[0]