# -*- encoding: utf-8 -*-
{
	'name': 'Reporte Asientos Contables',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_base_it','account_destinos_rep_it'],
	'version': '1.0',
	'description':"""
	Reporte en Excel para Asientos Contables
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'views/account_move.xml'
		],
	'installable': True
}
