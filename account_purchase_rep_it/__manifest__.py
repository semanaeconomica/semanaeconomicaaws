# -*- encoding: utf-8 -*-
{
	'name': 'Reporte REGISTRO DE COMPRAS',
	'category': 'account',
	'author': 'ITGRUPO',
	'depends': ['account_report_menu_it'],
	'version': '1.0',
	'description':"""
		Generar Reportes para REGISTRO DE COMPRAS
	""",
	'auto_install': False,
	'demo': [],
	'data':	[
		'security/ir.model.access.csv',
		'wizards/account_purchase_rep.xml',
		'views/account_purchase_book.xml'
	],
	'installable': True
}
