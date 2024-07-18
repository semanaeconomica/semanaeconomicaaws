# -*- encoding: utf-8 -*-
{
	'name': 'Account Credit Note',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account','account_fields_it'],
	'version': '1.0',
	'description':"""
	Funcionalidades para Notas de Credito
	""",
	'auto_install': False,
	'demo': [],
	'data':	['views/account_move_reversal.xml',
			 'views/account_move.xml'],
	'installable': True
}