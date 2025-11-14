# -*- encoding: utf-8 -*-
{
	'name': 'Pagos Multiples para SE',
	'category': 'account',
	'author': 'ITGRUPO-SE',
	'depends': ['account_multipayment_advance_it'],
	'version': '1.0',
	'description':"""
	- Pagos Multiples Advance SE
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move_line.xml',
		'views/multipayment_advance_it.xml'
	],
	'installable': True
}