# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO MAYOR ANALITICO',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para LIBRO MAYOR ANALITICO
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_higher_rep.xml',
		'views/account_higher_book.xml'
	],
	'installable': True
}
