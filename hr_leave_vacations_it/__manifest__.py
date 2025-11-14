# -*- encoding: utf-8 -*-
{
	'name': 'Vacaciones en ausencias',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_vacations_it','hr_leave_it'],
	'version': '1.0',
	'description':"""
		Vacaciones en ausencias
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizard/hr_vacation_rest_wizard.xml'
	],
	'installable': True
}