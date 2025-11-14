# -*- encoding: utf-8 -*-
{
	'name': 'Comisiones en RRHH',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
		Comisiones y bonos para planillas
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		# 'security/security.xml',
		'security/ir.model.access.csv',
		'views/hr_comission.xml',
		'views/hr_parameter_view.xml',
		# 'views/hr_vacation_role.xml',
		# 'views/hr_menus.xml'
	],
	'installable': True
}