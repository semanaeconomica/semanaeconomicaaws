# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime, sys, json
from odoo.http import request

class res_partner(models.Model):
    _inherit = 'res.partner'    

    id_culqi = fields.Char("Culqi Customer ID")