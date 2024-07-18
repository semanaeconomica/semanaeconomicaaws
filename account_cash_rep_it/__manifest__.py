# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO CAJA Y BANCOS',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para LIBRO CAJA Y BANCOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_cash_rep.xml',
		'views/account_cash_book.xml'
	],
	'installable': True
}
