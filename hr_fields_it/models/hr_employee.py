# -*- coding:utf-8 -*-
from odoo import api, fields, models

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	type_document_id = fields.Many2one('hr.type.document', string='Tipo de Documento')
	wage_bank_account_id = fields.Many2one('res.partner.bank', string='Cuenta Sueldo')
	cts_bank_account_id = fields.Many2one('res.partner.bank', string='Cuenta CTS')
	names = fields.Char(string='Nombres')
	last_name = fields.Char(string='Apellido Paterno')
	m_last_name = fields.Char(string='Apellido Materno')
	is_manager = fields.Boolean(string='Es un Director', default=False)
	condition = fields.Selection([('domiciled', 'Domiciliado'),
								  ('not_domiciled', 'No Domiciliado')], string='Condicion', default='domiciled')
	men = fields.Integer(string='Hijos Hombres')
	women = fields.Integer(string='Hijos Mujeres')
	address = fields.Char(string=u'Dirección')

	@api.onchange('names', 'last_name', 'm_last_name')
	def verify_name(self):
		self.name = '%s %s %s' % ((self.last_name or '').strip(), (self.m_last_name or '').strip(),(self.names or '').strip())

	def name_get(self):
		result = []
		for employee in self:
			name = '%s %s %s' % ((employee.last_name or '').strip(),(employee.m_last_name or '').strip(),(employee.names or '').strip())
			result.append([employee.id, name])
		return result
