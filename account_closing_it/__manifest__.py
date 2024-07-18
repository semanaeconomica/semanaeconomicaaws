# -*- encoding: utf-8 -*-
{
	'name': 'Cierre Contable It',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_fields_it'],
	'version': '1.0',
	'description':"""
	Sub-menu para creacion de Cierres Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/account_closing_it.xml'
		],
	'installable': True
}
