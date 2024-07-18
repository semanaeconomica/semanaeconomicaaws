# -*- encoding: utf-8 -*-
{
	'name': 'Hr Vacations',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
		Modulo de Vacaciones en Planilla
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_payslip.xml',
		'views/hr_vacation_control.xml',
		'views/hr_vacation_role.xml',
		'views/hr_menus.xml'
	],
	'installable': True
}