# -*- encoding: utf-8 -*-
{
	'name': 'Actualizar Cuentas Analiticas en Vista Tree',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Actualizar Cuenta Analitica
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move_line.xml',
		'views/account_analytic_line.xml',
		'wizards/update_account_analytic_wizard.xml'
	],
	'installable': True
}
