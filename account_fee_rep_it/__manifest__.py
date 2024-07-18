# -*- encoding: utf-8 -*-
{
	'name': 'Reporte LIBRO DE HONORARIOS',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para LIBRO DE HONORARIOS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_fee_rep.xml',
		'views/account_fee_book.xml'
	],
	'installable': True
}
