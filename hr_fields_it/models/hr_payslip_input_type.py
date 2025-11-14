# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrPayslipInputType(models.Model):
	_inherit = 'hr.payslip.input.type'

	company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.company.id)