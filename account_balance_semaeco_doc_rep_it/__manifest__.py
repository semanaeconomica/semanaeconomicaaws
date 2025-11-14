# -*- encoding: utf-8 -*-
{
	'name': 'fecha de cancelacion en reportes',
	'category': 'base',
	'author': 'ITGRUPO',
	'depends': ['account_balance_doc_advance_it','partner_receiver_fields_it'],
	'version': '1.0',
	'description':"""
	fecha de cancelacion en reportes
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_balance_period.xml',
		'views/account_move_view.xml'
		],
	'installable': True
}