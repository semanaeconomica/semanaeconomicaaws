# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE VENTAS',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para REGISTRO DE VENTAS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_sale_rep.xml',
		'views/account_sale_book.xml'
	],
	'installable': True
}
