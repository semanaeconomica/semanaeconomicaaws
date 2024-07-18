# -*- encoding: utf-8 -*-
{
	'name': 'Vista para Asientos Contables',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','account_base_it','account_fields_it'],
	'version': '1.0',
	'description':"""
	Sub-menu con vista para asientos contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move_view.xml'
		],
	'installable': True
}
