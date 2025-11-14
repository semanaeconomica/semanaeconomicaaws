from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime


class hr_vacation_rest_wizard(models.TransientModel):
	_name='hr.vacation.rest.wizard'

	year = fields.Char(u'Año')
	employee_id = fields.Many2one('hr.employee','Empleado', default=lambda self: self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)]) )
	showall = fields.Boolean('Mostrar Todos',default=False)

	def make_vacation_rest(self):
		self.env['hr.vacation.rest'].get_vacation_employee(self.year,self.employee_id,self.showall)
		name = 'Saldos de Vacaciones'
		return {
			'name': name,
			'type': 'ir.actions.act_window',
			'res_model': 'hr.vacation.rest',
			'view_type': 'form',
			'view_mode': 'tree',
			'views': [(False, 'tree')],
			'search_view_id':[self.env.ref('hr_vacations_it.hr_vacation_rest_search').id, 'search']
		}
