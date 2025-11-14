# -*- encoding: utf-8 -*-
{
	'name': 'Hr Importers IT',
	'category': 'hr',
	'author': 'ITGRUPO-HR',
	'depends': ['hr_fields_it'],
	'version': '1.0',
	'description':"""
	Module to place all functions to import data
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/hr_payslip.xml',
		'wizard/hr_import_wizard.xml',
		'wizard/hr_import_wd_wizard.xml',
		'views/hr_menus.xml',
			],
	'installable': True
}