# -*- encoding: utf-8 -*-
{
	'name': 'Reporte PERCEPCIONES',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para PERCEPCIONES
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_percep_rep.xml',
		'views/account_percep_book.xml',
		'views/account_percep_sp_book.xml'
	],
	'installable': True
}
