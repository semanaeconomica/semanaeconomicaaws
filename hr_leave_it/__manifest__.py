# -*- encoding: utf-8 -*-
{
	'name': 'Ausencias IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_holidays','hr_fields_it','hr_vacations'],
	'version': '1.0',
	'description':"""
	Registro de asuencias/vacaciones
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'views/hr_parameter_view.xml',
		'views/hr_leave.xml'
	],
	'installable': True
}