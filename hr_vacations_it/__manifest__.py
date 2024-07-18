# -*- encoding: utf-8 -*-
{
	'name': 'Hr Vacations it',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_vacations'],
	'version': '1.0',
	'description':"""
		Modulo de Vacaciones en Planilla por ITGrupo
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/hr_vacation_rest.xml',
		'wizard/hr_vacation_rest_wizard.xml'
	],
	'installable': True
}